"""OpenClaw websocket client service.

This module provides a generic RPC websocket client for OpenClaw and a pair
of convenience wrappers for prompt interactions.
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator, Mapping
from itertools import count
from typing import Any
from urllib.parse import urlparse

from websockets.exceptions import ConnectionClosed, WebSocketException
from websockets.legacy.client import (
    WebSocketClientProtocol,
)
from websockets.legacy.client import (
    connect as ws_connect,
)

from yumi.core.config import settings
from yumi.core.logger import logger

JSONDict = dict[str, Any]
StreamEvent = JSONDict | str


class OpenClawClient:
    """Async websocket client for OpenClaw.

    The client keeps a reusable websocket connection, reconnects automatically
    when the socket is closed, and supports a generic RPC call interface.
    """

    def __init__(
        self,
        *,
        claw_url: str | None = None,
        claw_port: int | None = None,
        timeout: int | None = None,
        prompt_method: str = "skills.status",
        extra_headers: Mapping[str, str] | None = None,
        max_retries: int = 2,
    ) -> None:
        self._claw_url = claw_url or settings.CLAW_URL
        self._claw_port = (
            claw_port if claw_port is not None else settings.CLAW_PORT
        )
        self._timeout = (
            timeout if timeout is not None else settings.CLAW_TIMEOUT
        )
        self._prompt_method = prompt_method
        self._extra_headers = dict(extra_headers) if extra_headers else None
        self._max_retries = max_retries

        self._ws: WebSocketClientProtocol | None = None
        self._connect_lock = asyncio.Lock()
        self._call_lock = asyncio.Lock()
        self._id_counter = count(1)

    @property
    def websocket_url(self) -> str:
        """Build websocket URL from settings fields."""
        parsed = urlparse(self._claw_url)

        if parsed.scheme in {"ws", "wss"}:
            scheme = parsed.scheme
            host = parsed.netloc or parsed.path
            if parsed.port:
                return f"{scheme}://{host}"
            return f"{scheme}://{host}:{self._claw_port}"

        if parsed.scheme in {"http", "https"}:
            scheme = "wss" if parsed.scheme == "https" else "ws"
            host = parsed.netloc
            if parsed.port:
                return f"{scheme}://{host}"
            return f"{scheme}://{host}:{self._claw_port}"

        host = self._claw_url.replace("//", "").strip("/")
        return f"ws://{host}:{self._claw_port}"

    async def connect(self) -> None:
        """Open websocket when needed and reuse active connection."""
        async with self._connect_lock:
            if self._is_connected:
                return

            logger.info(
                "[OpenClawClient] Connecting to %s",
                self.websocket_url,
            )
            try:
                self._ws = await ws_connect(
                    self.websocket_url,
                    extra_headers=self._extra_headers,
                    open_timeout=self._timeout,
                    close_timeout=self._timeout,
                )
            except (
                OSError,
                TimeoutError,
                WebSocketException,
            ):
                logger.error(
                    "[OpenClawClient] Failed to connect to %s",
                    self.websocket_url,
                    exc_info=True,
                )
                raise

            logger.info("[OpenClawClient] Connected")

    async def disconnect(self) -> None:
        """Close websocket connection and clear internal reference."""
        async with self._connect_lock:
            if not self._ws:
                return

            try:
                await asyncio.wait_for(self._ws.close(), timeout=self._timeout)
                logger.info("[OpenClawClient] Connection closed")
            except (
                ConnectionClosed,
                TimeoutError,
                WebSocketException,
                OSError,
            ):
                logger.warning(
                    "[OpenClawClient] Error while closing connection",
                    exc_info=True,
                )
            finally:
                self._ws = None

    async def call(
        self,
        method: str,
        params: JSONDict | None = None,
    ) -> JSONDict:
        """Call an OpenClaw RPC method and return first non-challenge event.

        Args:
            method: RPC method name.
            params: Method parameters.

        Returns:
            Parsed JSON event as dictionary.
        """
        payload: JSONDict = {
            "id": next(self._id_counter),
            "method": method,
            "params": params or {},
        }

        async with self._call_lock:
            for attempt in range(1, self._max_retries + 2):
                try:
                    ws = await self._get_connection()
                    await self._send_json(ws, payload)
                    return await self._wait_for_non_challenge_event(ws)
                except (ConnectionClosed, WebSocketException, TimeoutError):
                    logger.warning(
                        "[OpenClawClient] RPC call failed (attempt %s/%s)",
                        attempt,
                        self._max_retries + 1,
                        exc_info=True,
                    )
                    await self._reset_connection()
                    if attempt > self._max_retries:
                        raise

            raise RuntimeError(
                "[OpenClawClient] Unexpected RPC loop termination"
            )

    async def send_prompt(self, prompt: str) -> str:
        """Send a prompt using the configured prompt method.

        Since OpenClaw prompt contract is not finalized, this method wraps
        ``call`` and returns a best-effort text representation of the result.
        """
        response = await self.call(
            method=self._prompt_method,
            params={"prompt": prompt},
        )
        return self._stringify_response(response)

    async def stream_prompt(
        self,
        prompt: str,
    ) -> AsyncGenerator[StreamEvent, None]:
        """Stream websocket events for a prompt request.

        The generator yields incoming websocket events without assuming a fixed
        schema. Streaming ends when one of these conditions happens:
        - socket closes
        - event == "complete"
        - event == "done"
        - receive timeout
        """
        payload: JSONDict = {
            "id": next(self._id_counter),
            "method": self._prompt_method,
            "params": {"prompt": prompt},
        }

        for attempt in range(1, self._max_retries + 2):
            try:
                ws = await self._get_connection()
                await self._send_json(ws, payload)

                while True:
                    try:
                        event = await self._recv_event(
                            ws,
                            timeout=float(self._timeout),
                        )
                    except TimeoutError:
                        logger.warning(
                            "[OpenClawClient] Stream timeout reached"
                        )
                        return
                    except ConnectionClosed:
                        logger.warning(
                            "[OpenClawClient] Stream socket closed by server"
                        )
                        return

                    if isinstance(event, dict):
                        if event.get("event") == "connect.challenge":
                            logger.info(
                                "[OpenClawClient] Received "
                                "connect.challenge event"
                            )
                        yield event
                        if event.get("event") in {"complete", "done"}:
                            return
                    else:
                        yield event

            except (ConnectionClosed, WebSocketException, TimeoutError):
                logger.warning(
                    "[OpenClawClient] Stream failed (attempt %s/%s)",
                    attempt,
                    self._max_retries + 1,
                    exc_info=True,
                )
                await self._reset_connection()
                if attempt > self._max_retries:
                    raise

    async def _get_connection(self) -> WebSocketClientProtocol:
        """Return a valid websocket connection, reconnecting when needed."""
        if not self._is_connected:
            await self.connect()

        if not self._ws:
            raise RuntimeError(
                "[OpenClawClient] Websocket connection is unavailable"
            )

        return self._ws

    async def _reset_connection(self) -> None:
        """Force close current websocket reference for clean reconnect."""
        if self._ws is None:
            return

        try:
            await self._ws.close()
        except (ConnectionClosed, WebSocketException, OSError):
            logger.debug(
                "[OpenClawClient] Failed to close stale socket",
                exc_info=True,
            )
        finally:
            self._ws = None

    async def _send_json(
        self,
        ws: WebSocketClientProtocol,
        payload: JSONDict,
    ) -> None:
        """Serialize and send JSON payload through websocket."""
        body = json.dumps(payload)
        await asyncio.wait_for(ws.send(body), timeout=self._timeout)

    async def _wait_for_non_challenge_event(
        self,
        ws: WebSocketClientProtocol,
    ) -> JSONDict:
        """Receive messages until the first non-connect.challenge event."""
        deadline = asyncio.get_running_loop().time() + float(self._timeout)

        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                raise TimeoutError(
                    "[OpenClawClient] Timed out waiting for RPC response"
                )

            event = await self._recv_event(ws, timeout=remaining)
            if (
                isinstance(event, dict)
                and event.get("event") == "connect.challenge"
            ):
                logger.info(
                    "[OpenClawClient] Received connect.challenge event"
                )
                continue

            if isinstance(event, dict):
                return event

            return {"type": "raw", "payload": event}

    async def _recv_event(
        self,
        ws: WebSocketClientProtocol,
        *,
        timeout: float,
    ) -> StreamEvent:
        """Receive and decode one websocket event."""
        raw = await asyncio.wait_for(ws.recv(), timeout=timeout)

        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="replace")

        if not isinstance(raw, str):
            return str(raw)

        try:
            parsed: StreamEvent = json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("[OpenClawClient] Non-JSON event received")
            return raw

        return parsed

    @property
    def _is_connected(self) -> bool:
        """Tell whether websocket is currently open."""
        return bool(self._ws and not self._ws.closed)

    @staticmethod
    def _stringify_response(response: JSONDict) -> str:
        """Extract best-effort textual content from a generic RPC response."""
        for key in ("response", "result", "text", "message", "content"):
            value = response.get(key)
            if isinstance(value, str):
                return value

        return json.dumps(response, ensure_ascii=False)
