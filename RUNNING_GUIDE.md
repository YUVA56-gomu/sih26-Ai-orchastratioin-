# 🌊 SAMUDRA AI — Quick Start & Execution Guide

This guide provides step-by-step instructions to properly run and test SAMUDRA AI on your system.

---

## 🚀 Quick Start (2-Step Launch)

Open your terminal in the repository root directory (`d:\Oscorp\sih`):

### Terminal 1: Start Python Backend Server
```powershell
python -m uvicorn api.samudra_api:app --reload --port 8000
```
- **Backend API**: [`http://localhost:8000`](http://localhost:8000)
- **Interactive Swagger Docs**: [`http://localhost:8000/docs`](http://localhost:8000/docs)
- **Health Endpoint**: [`http://localhost:8000/health`](http://localhost:8000/health)

---

### Terminal 2: Start Web Frontend Application
```powershell
npm --prefix web run dev
```
- **Web Interface**: [`http://localhost:5173`](http://localhost:5173)

---

## 🤖 Local Ollama Setup (Optional / Configured)

If you are using local LLM inference (`LLM_PROVIDER=ollama` in `.env`):

1. **Check installed Ollama models**:
   ```powershell
   ollama list
   ```
2. **Ensure `llama3.1:8b` is installed**:
   ```powershell
   ollama pull llama3.1:8b
   ```
   > **Note**: Windows automatically runs Ollama as a background service on port `11434`. You do **not** need to manually run `ollama serve`.

---

## ⚙️ Switching LLM Providers (`.env`)

You can switch the primary AI brain anytime by modifying `LLM_PROVIDER` in your `.env` file:

```env
# Options: ollama | groq | gemini | mock
LLM_PROVIDER=ollama

# Timeout settings (for slow CPU inference)
OLLAMA_TIMEOUT_SECONDS=120
```

### Automatic Fallback & Circuit Breaker Architecture:
SAMUDRA AI implements an automatic failover circuit breaker:
- Primary Provider (`Ollama`) ➔ `Groq` ➔ `Gemini` ➔ `FallbackMock`

If your local Ollama CPU inference takes longer than 120s or fails, SAMUDRA automatically falls back to Groq or Gemini without interrupting the user conversation stream.

---

## 🧪 Testing & Building

### Run Backend Unit Tests (150 tests)
```powershell
python -m pytest tests/
```

### Build Web Production Bundle
```powershell
npm --prefix web run build
```

---

## 💡 Troubleshooting & Tips

- **Ollama Timeout or Slow CPU Inference**:
  - `llama3.1:8b` is a 4.9 GB model. On CPU, inference takes 30-45 seconds per query.
  - For **faster local responses (<5s)**, try pulling a smaller CPU-friendly model:
    ```powershell
    ollama pull qwen2.5:3b
    ```
    Then update `.env`: `OLLAMA_MODEL=qwen2.5:3b`.
- **`bind: address already in use` error when running `ollama serve`**:
  - This is expected on Windows because Ollama is already running as a system service.
