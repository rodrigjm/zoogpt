/**
 * MSW handlers for API mocking in tests
 */
import { http, HttpResponse } from 'msw';

const API_BASE = '/api';

export const handlers = [
  // POST /api/session - Create new session
  http.post(`${API_BASE}/session`, async () => {
    return HttpResponse.json({
      session_id: 'test-session-123',
      created_at: new Date().toISOString(),
      client_type: 'web',
      metadata: {},
    });
  }),

  // GET /api/session/:id - Get session info
  http.get(`${API_BASE}/session/:id`, ({ params }) => {
    return HttpResponse.json({
      session_id: params.id,
      created_at: new Date().toISOString(),
      client_type: 'web',
      metadata: {},
    });
  }),

  // POST /api/chat/stream - Stream chat response (SSE)
  http.post(`${API_BASE}/chat/stream`, async ({ request }) => {
    const body = await request.json();
    const message = (body as any).message;

    // Create SSE stream response
    const encoder = new TextEncoder();
    const stream = new ReadableStream({
      start(controller) {
        // Send text chunks
        const chunks = ['Hello ', 'from ', 'the ', 'zoo!'];
        chunks.forEach((chunk) => {
          const data = `data: ${JSON.stringify({ type: 'text', content: chunk })}\n\n`;
          controller.enqueue(encoder.encode(data));
        });

        // Send done event with metadata
        const doneData = `data: ${JSON.stringify({
          type: 'done',
          followup_questions: [
            'What do they eat?',
            'Where do they live?',
          ],
          sources: [
            {
              title: 'Animal Facts',
              url: '/docs/animals',
              snippet: 'Information about zoo animals',
            },
          ],
        })}\n\n`;
        controller.enqueue(encoder.encode(doneData));

        controller.close();
      },
    });

    return new HttpResponse(stream, {
      headers: {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      },
    });
  }),

  // POST /api/chat - Non-streaming chat
  http.post(`${API_BASE}/chat`, async ({ request }) => {
    const body = await request.json();
    return HttpResponse.json({
      session_id: (body as any).session_id,
      message_id: 'msg-123',
      reply: 'Hello from the zoo!',
      sources: [],
      created_at: new Date().toISOString(),
    });
  }),

  // POST /api/voice/stt - Speech-to-text
  http.post(`${API_BASE}/voice/stt`, async ({ request }) => {
    const formData = await request.formData();
    const sessionId = formData.get('session_id');

    return HttpResponse.json({
      session_id: sessionId,
      text: 'Tell me about the lions',
    });
  }),

  // POST /api/voice/tts - Text-to-speech
  http.post(`${API_BASE}/voice/tts`, async () => {
    // Return mock audio blob (empty wav header)
    const mockAudioData = new Uint8Array([
      0x52, 0x49, 0x46, 0x46, // "RIFF"
      0x24, 0x00, 0x00, 0x00, // chunk size
      0x57, 0x41, 0x56, 0x45, // "WAVE"
      0x66, 0x6d, 0x74, 0x20, // "fmt "
      0x10, 0x00, 0x00, 0x00, // subchunk1 size
      0x01, 0x00, 0x01, 0x00, // audio format, num channels
      0x44, 0xac, 0x00, 0x00, // sample rate
      0x88, 0x58, 0x01, 0x00, // byte rate
      0x02, 0x00, 0x10, 0x00, // block align, bits per sample
      0x64, 0x61, 0x74, 0x61, // "data"
      0x00, 0x00, 0x00, 0x00, // subchunk2 size
    ]);

    return HttpResponse.arrayBuffer(mockAudioData.buffer, {
      headers: {
        'Content-Type': 'audio/wav',
      },
    });
  }),

  // GET /api/health - Health check
  http.get(`${API_BASE}/health`, () => {
    return HttpResponse.json({ ok: true });
  }),
];
