"""Testes unitários do módulo de métricas."""

from yumi.core import metrics


def setup_function():
    metrics.reset_metrics()


def test_contadores_incrementam_corretamente():
    metrics.record_chat_request()
    metrics.record_stream_request()
    metrics.record_openclaw_success()
    metrics.record_openclaw_fallback()
    metrics.record_openclaw_error()

    snapshot = metrics.get_metrics_snapshot()

    assert snapshot.chat_requests_total == 1
    assert snapshot.chat_stream_requests_total == 1
    assert snapshot.chat_openclaw_success_total == 1
    assert snapshot.chat_openclaw_fallback_total == 1
    assert snapshot.chat_openclaw_errors_total == 1


def test_latencia_e_duracao_sao_registradas():
    metrics.record_chat_latency(0.25)
    metrics.record_stream_duration(1.5)

    snapshot = metrics.get_metrics_snapshot()

    assert snapshot.chat_response_time_seconds == (0.25,)
    assert snapshot.chat_stream_duration_seconds == (1.5,)


def test_tamanho_da_resposta_e_registrado():
    metrics.record_response_size(42)

    snapshot = metrics.get_metrics_snapshot()

    assert snapshot.chat_response_size_chars == (42,)


def test_snapshot_e_reset_funcionam():
    metrics.record_chat_request()
    metrics.record_chat_latency(0.1)
    metrics.record_response_size(3)

    before = metrics.get_metrics_snapshot()
    assert before.chat_requests_total == 1
    assert before.chat_response_time_seconds == (0.1,)
    assert before.chat_response_size_chars == (3,)

    metrics.reset_metrics()
    after = metrics.get_metrics_snapshot()

    assert after.chat_requests_total == 0
    assert after.chat_stream_requests_total == 0
    assert after.chat_openclaw_success_total == 0
    assert after.chat_openclaw_fallback_total == 0
    assert after.chat_openclaw_errors_total == 0
    assert after.chat_response_time_seconds == ()
    assert after.chat_stream_duration_seconds == ()
    assert after.chat_response_size_chars == ()
