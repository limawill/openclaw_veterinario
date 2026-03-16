"""Métricas em memória para observabilidade do chat.

Este módulo oferece contadores e séries simples em memória para permitir
instrumentação sem dependências externas.
"""

# pylint: disable=global-statement

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from threading import Lock

from yumi.core.logger import logger


@dataclass(frozen=True)
class MetricsSnapshot:
    """Snapshot imutável das métricas atuais."""

    chat_requests_total: int
    chat_stream_requests_total: int
    chat_openclaw_success_total: int
    chat_openclaw_fallback_total: int
    chat_openclaw_errors_total: int
    chat_response_time_seconds: tuple[float, ...]
    chat_stream_duration_seconds: tuple[float, ...]
    chat_response_size_chars: tuple[int, ...]


_lock = Lock()

_chat_requests_total = 0
_chat_stream_requests_total = 0
_chat_openclaw_success_total = 0
_chat_openclaw_fallback_total = 0
_chat_openclaw_errors_total = 0

_chat_response_time_seconds: list[float] = []
_chat_stream_duration_seconds: list[float] = []
_chat_response_size_chars: list[int] = []


def _append_float(series: list[float], value: float) -> None:
    """Adiciona float normalizado e loga evento de métrica."""
    normalized = max(float(value), 0.0)
    series.append(normalized)


def _append_int(series: list[int], value: int) -> None:
    """Adiciona inteiro não-negativo e loga evento de métrica."""
    normalized = max(int(value), 0)
    series.append(normalized)


def record_chat_request() -> None:
    """Incrementa total de requisições do endpoint /chat."""
    global _chat_requests_total
    with _lock:
        _chat_requests_total += 1
        logger.info(
            "[metrics] chat_requests_total=%s",
            _chat_requests_total,
        )


def record_stream_request() -> None:
    """Incrementa total de requisições do endpoint /chat/stream."""
    global _chat_stream_requests_total
    with _lock:
        _chat_stream_requests_total += 1
        logger.info(
            "[metrics] chat_stream_requests_total=%s",
            _chat_stream_requests_total,
        )


def record_openclaw_success() -> None:
    """Incrementa total de respostas OpenClaw bem-sucedidas."""
    global _chat_openclaw_success_total
    with _lock:
        _chat_openclaw_success_total += 1
        logger.info(
            "[metrics] chat_openclaw_success_total=%s",
            _chat_openclaw_success_total,
        )


def record_openclaw_fallback() -> None:
    """Incrementa total de fallbacks para YumiAgent."""
    global _chat_openclaw_fallback_total
    with _lock:
        _chat_openclaw_fallback_total += 1
        logger.info(
            "[metrics] chat_openclaw_fallback_total=%s",
            _chat_openclaw_fallback_total,
        )


def record_openclaw_error() -> None:
    """Incrementa total de erros na integração com OpenClaw."""
    global _chat_openclaw_errors_total
    with _lock:
        _chat_openclaw_errors_total += 1
        logger.info(
            "[metrics] chat_openclaw_errors_total=%s",
            _chat_openclaw_errors_total,
        )


def record_chat_latency(seconds: float) -> None:
    """Registra latência de execução do fluxo /chat."""
    with _lock:
        _append_float(_chat_response_time_seconds, seconds)
        logger.info(
            "[metrics] chat_response_time_seconds=%s",
            _chat_response_time_seconds[-1],
        )


def record_stream_duration(seconds: float) -> None:
    """Registra duração total de execução do fluxo /chat/stream."""
    with _lock:
        _append_float(_chat_stream_duration_seconds, seconds)
        logger.info(
            "[metrics] chat_stream_duration_seconds=%s",
            _chat_stream_duration_seconds[-1],
        )


def record_response_size(chars: int) -> None:
    """Registra tamanho final da resposta em caracteres."""
    with _lock:
        _append_int(_chat_response_size_chars, chars)
        logger.info(
            "[metrics] chat_response_size_chars=%s",
            _chat_response_size_chars[-1],
        )


def get_metrics_snapshot() -> MetricsSnapshot:
    """Retorna snapshot imutável das métricas atuais."""
    with _lock:
        return MetricsSnapshot(
            chat_requests_total=_chat_requests_total,
            chat_stream_requests_total=_chat_stream_requests_total,
            chat_openclaw_success_total=_chat_openclaw_success_total,
            chat_openclaw_fallback_total=_chat_openclaw_fallback_total,
            chat_openclaw_errors_total=_chat_openclaw_errors_total,
            chat_response_time_seconds=tuple(_chat_response_time_seconds),
            chat_stream_duration_seconds=tuple(_chat_stream_duration_seconds),
            chat_response_size_chars=tuple(_chat_response_size_chars),
        )


def reset_metrics() -> None:
    """Reseta métricas em memória (uso principal: testes)."""
    global _chat_requests_total
    global _chat_stream_requests_total
    global _chat_openclaw_success_total
    global _chat_openclaw_fallback_total
    global _chat_openclaw_errors_total

    with _lock:
        _chat_requests_total = 0
        _chat_stream_requests_total = 0
        _chat_openclaw_success_total = 0
        _chat_openclaw_fallback_total = 0
        _chat_openclaw_errors_total = 0

        _chat_response_time_seconds.clear()
        _chat_stream_duration_seconds.clear()
        _chat_response_size_chars.clear()


def get_series_lengths() -> tuple[int, int, int]:
    """Retorna tamanhos das séries de métricas temporais."""
    snapshot = get_metrics_snapshot()
    return (
        len(snapshot.chat_response_time_seconds),
        len(snapshot.chat_stream_duration_seconds),
        len(snapshot.chat_response_size_chars),
    )


def latest_values() -> tuple[float | None, float | None, int | None]:
    """Retorna últimos valores registrados para inspeção rápida."""
    snapshot = get_metrics_snapshot()

    def _last_or_none(values: Sequence[float] | Sequence[int]):
        return values[-1] if values else None

    return (
        _last_or_none(snapshot.chat_response_time_seconds),
        _last_or_none(snapshot.chat_stream_duration_seconds),
        _last_or_none(snapshot.chat_response_size_chars),
    )
