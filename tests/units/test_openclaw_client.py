"""Testes unitarios para yumi/services/openclaw_client.py."""

# pylint: disable=protected-access

import json
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from yumi.services.openclaw_client import OpenClawClient


class TestOpenClawClientUnit:
    """Cobertura da logica isolada do cliente via mocks."""

    def test_websocket_url_converte_http_para_ws(self):
        client = OpenClawClient(claw_url="http://127.0.0.1", claw_port=9999)
        assert client.websocket_url == "ws://127.0.0.1:9999"

    def test_websocket_url_respeita_ws_com_porta(self):
        client = OpenClawClient(claw_url="ws://localhost:8765", claw_port=9999)
        assert client.websocket_url == "ws://localhost:8765"

    @pytest.mark.asyncio
    async def test_send_prompt_usa_wrapper_call(self):
        client = OpenClawClient(prompt_method="skills.status")
        client.call = AsyncMock(return_value={"result": "ok"})

        result = await client.send_prompt("teste prompt")

        assert result == "ok"
        client.call.assert_awaited_once_with(
            method="skills.status",
            params={"prompt": "teste prompt"},
        )

    @pytest.mark.asyncio
    async def test_call_faz_retry_apos_timeout(self):
        client = OpenClawClient(max_retries=1)
        ws = SimpleNamespace()

        client._get_connection = AsyncMock(return_value=ws)
        client._send_json = AsyncMock(side_effect=[TimeoutError(), None])
        client._wait_for_non_challenge_event = AsyncMock(
            return_value={"result": "ok"}
        )
        client._reset_connection = AsyncMock()

        result = await client.call("skills.status", {})

        assert result == {"result": "ok"}
        assert client._send_json.await_count == 2
        client._reset_connection.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_stream_prompt_yielda_eventos_ate_done(self):
        client = OpenClawClient(prompt_method="stream.test")
        ws = SimpleNamespace()

        client._get_connection = AsyncMock(return_value=ws)
        client._send_json = AsyncMock()
        client._recv_event = AsyncMock(
            side_effect=[
                {"type": "event", "event": "connect.challenge"},
                {"type": "event", "event": "chunk", "payload": "A"},
                {"type": "event", "event": "done"},
            ]
        )

        events = [event async for event in client.stream_prompt("ola")]

        assert [e["event"] for e in events] == [
            "connect.challenge",
            "chunk",
            "done",
        ]
        client._send_json.assert_awaited_once()

    def test_stringify_response_fallback_json(self):
        payload = {"foo": "bar", "num": 1}
        out = OpenClawClient._stringify_response(payload)
        assert out == json.dumps(payload, ensure_ascii=False)
