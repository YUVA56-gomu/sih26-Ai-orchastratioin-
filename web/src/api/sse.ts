import { AgentStepPayload, Artifact, ChatResponse } from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

export interface StreamHandlers {
  onStart?: (data: { conversation_id: string; thread_id: string; query: string }) => void;
  onAgentStep?: (step: AgentStepPayload) => void;
  onArtifact?: (artifact: Artifact) => void;
  onResponseChunk?: (chunk: { content: string; incremental: boolean }) => void;
  onDone?: (data: ChatResponse) => void;
  onError?: (error: { error: string }) => void;
}

export function startChatStream(
  message: string,
  convId?: string,
  lat?: number,
  lon?: number,
  handlers: StreamHandlers = {}
): () => void {
  const controller = new AbortController();

  const payload = {
    message,
    conversation_id: convId,
    latitude: lat,
    longitude: lon,
  };

  fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
    signal: controller.signal,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Streaming failed (${response.status})`);
      }
      if (!response.body) {
        throw new Error('ReadableStream not supported');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      function read() {
        reader.read().then(({ done, value }) => {
          if (done) return;
          buffer += decoder.decode(value, { stream: true });

          const lines = buffer.split('\n');
          buffer = lines.pop() || ''; // Keep incomplete line in buffer

          let currentEvent = 'message';

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed) continue;

            if (trimmed.startsWith('event:')) {
              currentEvent = trimmed.replace('event:', '').trim();
            } else if (trimmed.startsWith('data:')) {
              const rawData = trimmed.replace('data:', '').trim();
              try {
                const parsed = JSON.parse(rawData);
                if (currentEvent === 'start' && handlers.onStart) {
                  handlers.onStart(parsed);
                } else if ((currentEvent === 'node' || currentEvent === 'agent_step') && handlers.onAgentStep) {
                  handlers.onAgentStep(parsed);
                } else if (currentEvent === 'artifact' && handlers.onArtifact) {
                  handlers.onArtifact(parsed.artifact || parsed);
                } else if (currentEvent === 'response' && handlers.onResponseChunk) {
                  handlers.onResponseChunk(parsed);
                } else if (currentEvent === 'done' && handlers.onDone) {
                  handlers.onDone(parsed);
                } else if (currentEvent === 'error' && handlers.onError) {
                  handlers.onError(parsed);
                }
              } catch (e) {
                console.warn('Failed to parse SSE payload:', rawData, e);
              }
            }
          }

          read();
        }).catch((err) => {
          if (err.name !== 'AbortError' && handlers.onError) {
            handlers.onError({ error: err.message || 'Stream processing failed' });
          }
        });
      }

      read();
    })
    .catch((err) => {
      if (err.name !== 'AbortError' && handlers.onError) {
        handlers.onError({ error: err.message || 'Network connection failed' });
      }
    });

  return () => {
    controller.abort();
  };
}
