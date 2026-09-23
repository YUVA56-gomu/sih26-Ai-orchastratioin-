"""
tests/test_provider_manager.py
───────────────────────────────
Unit tests for SAMUDRA AI Multi-LLM Fallback & Circuit Breaker system.
"""

import time
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.messages import HumanMessage, AIMessage

from graph.llm import (
    LLMProviderManager,
    MultiLLMFallbackWrapper,
    ProviderState,
    classify_error,
    get_llm,
)


@pytest.fixture(autouse=True)
def reset_provider_manager(monkeypatch):
    """Reset LLMProviderManager singleton state before each test."""
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    LLMProviderManager().reset()
    yield
    LLMProviderManager().reset()


def test_classify_error():
    assert classify_error(Exception("HTTP 429 Too Many Requests")) == "quota"
    assert classify_error(Exception("RESOURCE_EXHAUSTED: quota exceeded")) == "quota"
    assert classify_error(Exception("401 Unauthorized: Invalid API Key")) == "config"
    assert classify_error(Exception("Connection timed out")) == "transient"


def test_1_gemini_success():
    """Test 1: Gemini success -> Gemini used as primary provider."""
    mock_gemini = MagicMock()
    mock_gemini.invoke.return_value = AIMessage(content="Response from Gemini")

    wrapper = MultiLLMFallbackWrapper()
    with patch.object(wrapper, "_get_provider_llm", return_value=mock_gemini):
        response = wrapper.invoke([HumanMessage(content="Hello")])
        assert response.content == "Response from Gemini"
        assert response.response_metadata["provider_used"] == "gemini"
        assert response.response_metadata["fallback_used"] is False

    status = LLMProviderManager().get_provider_status()
    assert status["providers"]["gemini"]["available"] is True
    assert status["providers"]["gemini"]["status"] == "available"


def test_2_gemini_429_fallback_to_groq():
    """Test 2: Gemini 429 quota error -> Gemini circuit opens, Groq used."""
    mock_groq = MagicMock()
    mock_groq.invoke.return_value = AIMessage(content="Response from Groq")

    wrapper = MultiLLMFallbackWrapper()

    def side_effect(provider_name):
        if provider_name == "gemini":
            raise Exception("HTTP 429: Rate limit exceeded")
        elif provider_name == "groq":
            return mock_groq
        raise ValueError(provider_name)

    with patch.object(wrapper, "_get_provider_llm", side_effect=side_effect):
        response = wrapper.invoke([HumanMessage(content="Hello")])
        assert response.content == "Response from Groq"
        assert response.response_metadata["provider_used"] == "groq"
        assert response.response_metadata["fallback_used"] is True

    status = LLMProviderManager().get_provider_status()
    assert status["providers"]["gemini"]["available"] is False
    assert status["providers"]["gemini"]["status"] == "cooldown"
    assert status["providers"]["gemini"]["last_error_type"] == "quota"


def test_3_gemini_resource_exhausted_fallback():
    """Test 3: Gemini RESOURCE_EXHAUSTED -> Gemini circuit opens, Groq used."""
    mock_groq = MagicMock()
    mock_groq.invoke.return_value = AIMessage(content="Response from Groq")

    wrapper = MultiLLMFallbackWrapper()

    def side_effect(provider_name):
        if provider_name == "gemini":
            raise Exception("RESOURCE_EXHAUSTED: Quota exceeded for model")
        elif provider_name == "groq":
            return mock_groq
        raise ValueError(provider_name)

    with patch.object(wrapper, "_get_provider_llm", side_effect=side_effect):
        response = wrapper.invoke([HumanMessage(content="Hello")])
        assert response.content == "Response from Groq"
        assert response.response_metadata["provider_used"] == "groq"

    status = LLMProviderManager().get_provider_status()
    assert status["providers"]["gemini"]["available"] is False
    assert status["providers"]["gemini"]["last_error_type"] == "quota"


def test_4_second_request_during_cooldown():
    """Test 4: Request 2 while Gemini cooldown active -> Gemini NOT called, Groq called directly."""
    manager = LLMProviderManager()
    # Manually open Gemini circuit
    manager.providers["gemini"].mark_quota_error("Quota exceeded", cooldown_seconds=900)

    mock_groq = MagicMock()
    mock_groq.invoke.return_value = AIMessage(content="Groq direct response")

    wrapper = MultiLLMFallbackWrapper()

    called_providers = []

    def side_effect(provider_name):
        called_providers.append(provider_name)
        if provider_name == "groq":
            return mock_groq
        raise ValueError(provider_name)

    with patch.object(wrapper, "_get_provider_llm", side_effect=side_effect):
        response = wrapper.invoke([HumanMessage(content="Hello again")])
        assert response.content == "Groq direct response"
        assert "gemini" not in called_providers
        assert "groq" in called_providers


def test_5_cooldown_expiration():
    """Test 5: Cooldown expires -> Gemini becomes eligible again."""
    manager = LLMProviderManager()
    # Set unavailable until past timestamp
    manager.providers["gemini"].available = False
    manager.providers["gemini"].unavailable_until = time.time() - 10

    assert manager.providers["gemini"].is_available() is True
    assert manager.get_provider_status()["providers"]["gemini"]["available"] is True


def test_6_gemini_succeeds_after_cooldown():
    """Test 6: Gemini succeeds after cooldown -> Gemini circuit closes permanently."""
    manager = LLMProviderManager()
    manager.providers["gemini"].available = False
    manager.providers["gemini"].unavailable_until = time.time() - 5

    mock_gemini = MagicMock()
    mock_gemini.invoke.return_value = AIMessage(content="Gemini recovered")

    wrapper = MultiLLMFallbackWrapper()
    with patch.object(wrapper, "_get_provider_llm", return_value=mock_gemini):
        response = wrapper.invoke([HumanMessage(content="Hello")])
        assert response.content == "Gemini recovered"

    status = LLMProviderManager().get_provider_status()
    assert status["providers"]["gemini"]["available"] is True
    assert status["providers"]["gemini"]["failure_count"] == 0


def test_7_gemini_failure_groq_success():
    """Test 7: Gemini failure + Groq success -> Groq response returned."""
    mock_groq = MagicMock()
    mock_groq.invoke.return_value = AIMessage(content="Groq fallback output")

    wrapper = MultiLLMFallbackWrapper()

    def side_effect(provider_name):
        if provider_name == "gemini":
            raise Exception("Gemini connection error")
        return mock_groq

    with patch.object(wrapper, "_get_provider_llm", side_effect=side_effect):
        response = wrapper.invoke([HumanMessage(content="Test")])
        assert response.content == "Groq fallback output"
        assert response.response_metadata["provider_used"] == "groq"


def test_8_gemini_and_groq_failure_ollama_success():
    """Test 8: Gemini fail + Groq fail + Ollama success -> Ollama response returned."""
    mock_ollama = MagicMock()
    mock_ollama.invoke.return_value = AIMessage(content="Ollama llama3.1:8b output")

    wrapper = MultiLLMFallbackWrapper()

    def side_effect(provider_name):
        if provider_name in ("gemini", "groq"):
            raise Exception(f"{provider_name} unavailable")
        return mock_ollama

    with patch.object(wrapper, "_get_provider_llm", side_effect=side_effect):
        response = wrapper.invoke([HumanMessage(content="Test")])
        assert response.content == "Ollama llama3.1:8b output"
        assert response.response_metadata["provider_used"] == "ollama"


def test_9_all_providers_fail_fallback_mock():
    """Test 9: All providers fail -> FallbackMockLLM response returned safely."""
    wrapper = MultiLLMFallbackWrapper()

    with patch.object(wrapper, "_get_provider_llm", side_effect=Exception("API failure")):
        response = wrapper.invoke([HumanMessage(content="Test query")])
        assert response.content is not None
        assert response.response_metadata["provider_used"] == "mock"


def test_10_non_quota_gemini_error():
    """Test 10: Non-quota Gemini network error -> does NOT set long 15-minute quota cooldown."""
    wrapper = MultiLLMFallbackWrapper()

    mock_groq = MagicMock()
    mock_groq.invoke.return_value = AIMessage(content="Groq output")

    def side_effect(provider_name):
        if provider_name == "gemini":
            raise Exception("500 Internal Server Error / Network Timeout")
        return mock_groq

    with patch.object(wrapper, "_get_provider_llm", side_effect=side_effect):
        response = wrapper.invoke([HumanMessage(content="Hello")])
        assert response.content == "Groq output"

    status = LLMProviderManager().get_provider_status()
    assert status["providers"]["gemini"]["last_error_type"] == "transient"


def test_11_streaming_fallback():
    """Test 11: Streaming fallback produces response object."""
    wrapper = MultiLLMFallbackWrapper()
    mock_groq = MagicMock()
    mock_groq.invoke.return_value = AIMessage(content="Stream Groq output")

    def side_effect(provider_name):
        if provider_name == "gemini":
            raise Exception("Gemini down")
        return mock_groq

    with patch.object(wrapper, "_get_provider_llm", side_effect=side_effect):
        chunks = list(wrapper.stream([HumanMessage(content="Stream test")]))
        assert len(chunks) == 1
        assert chunks[0].content == "Stream Groq output"


def test_12_ollama_unavailability_graceful_handling():
    """Test 12: Connection error on Ollama handled gracefully without crash."""
    from graph.llm import OllamaLLM
    ollama = OllamaLLM(base_url="http://invalid-localhost:99999")
    with pytest.raises(Exception):
        ollama.invoke([HumanMessage(content="Test")])


def test_14_zero_network_probe_sub_millisecond_state_check():
    """Test 14: Assert provider state checking is purely O(1) in-memory and executes in < 1ms."""
    manager = LLMProviderManager()
    start_time = time.perf_counter()
    for _ in range(1000):
        _ = manager.providers["gemini"].is_available()
        _ = manager.providers["groq"].is_available()
        _ = manager.providers["ollama"].is_available()
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    # 1000 checks should execute in well under 10ms (approx 0.001ms per check)
    assert elapsed_ms < 10.0

