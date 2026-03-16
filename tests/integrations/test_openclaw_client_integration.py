"""Testes de integracao para OpenClawClient com servidor websocket local."""

import json

import pytest
import pytest_asyncio
from websockets.exceptions import ConnectionClosed
from websockets.legacy.server import WebSocketServerProtocol, serve

from yumi.services.openclaw_client import OpenClawClient


@pytest_asyncio.fixture(name="openclaw_mock_server")
async def _openclaw_mock_server(unused_tcp_port):
    """Sobe servidor websocket local para exercitar o cliente ponta a ponta."""

    async def handler(ws: WebSocketServerProtocol):
        try:
            while True:
                raw = await ws.recv()
                request = json.loads(raw)
                method = request.get("method")

                if method == "skills.status":
                    await ws.send(
                        json.dumps(
                            {
                                "type": "event",
                                "event": "connect.challenge",
                                "payload": {},
                            }
                        )
                    )
                    await ws.send(
                        json.dumps(
                            {
                                "type": "result",
                                "result": "status-ok",
                            }
                        )
                    )

                elif method == "stream.test":
                    await ws.send(
                        json.dumps(
                            {
                                "type": "event",
                                "event": "connect.challenge",
                            }
                        )
                    )
                    await ws.send(
                        json.dumps(
                            {
                                "type": "event",
                                "event": "chunk",
                                "payload": "primeiro",
                            }
                        )
                    )
                    await ws.send(
                        json.dumps(
                            {
                                "type": "event",
                                "event": "done",
                            }
                        )
                    )

                elif method == "close.after.response":
                    await ws.send(
                        json.dumps({"type": "result", "result": "ok"})
                    )
                    await ws.close()

                else:
                    await ws.send(
                        json.dumps({"type": "result", "echo": request})
                    )
        except ConnectionClosed:
            return

    server = await serve(handler, "127.0.0.1", unused_tcp_port)
    uri = f"ws://127.0.0.1:{unused_tcp_port}"

    try:
        yield uri
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.asyncio
async def test_call_ignora_connect_challenge(openclaw_mock_server):
    client = OpenClawClient(
        claw_url=openclaw_mock_server,
        timeout=2,
    )

    try:
        response = await client.call("skills.status", {})
    finally:
        await client.disconnect()

    assert response == {"type": "result", "result": "status-ok"}


@pytest.mark.asyncio
async def test_stream_prompt_yielda_eventos_ate_done(openclaw_mock_server):
    client = OpenClawClient(
        claw_url=openclaw_mock_server,
        timeout=2,
        prompt_method="stream.test",
    )

    try:
        events = [event async for event in client.stream_prompt("mensagem")]
    finally:
        await client.disconnect()

    assert [event["event"] for event in events] == [
        "connect.challenge",
        "chunk",
        "done",
    ]


@pytest.mark.asyncio
async def test_reconecta_automaticamente_entre_chamadas(openclaw_mock_server):
    client = OpenClawClient(
        claw_url=openclaw_mock_server,
        timeout=2,
        max_retries=2,
    )

    try:
        first = await client.call("close.after.response", {})
        second = await client.call("skills.status", {})
    finally:
        await client.disconnect()

    assert first == {"type": "result", "result": "ok"}
    assert second == {"type": "result", "result": "status-ok"}
