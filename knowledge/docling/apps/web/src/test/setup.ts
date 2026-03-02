import '@testing-library/jest-dom';
import { vi, beforeAll, afterEach, afterAll } from 'vitest';
import { server } from './mocks/server';

// Start MSW server before all tests
beforeAll(() => server.listen({ onUnhandledRequest: 'warn' }));

// Reset handlers after each test
afterEach(() => server.resetHandlers());

// Clean up after all tests
afterAll(() => server.close());

// Mock MediaRecorder
const mockMediaRecorder = {
  start: vi.fn(),
  stop: vi.fn(),
  pause: vi.fn(),
  resume: vi.fn(),
  ondataavailable: null as ((event: { data: Blob }) => void) | null,
  onstop: null as (() => void) | null,
  onerror: null as ((event: Event) => void) | null,
  state: 'inactive' as RecordingState,
};

class MockMediaRecorder {
  ondataavailable = null as ((event: { data: Blob }) => void) | null;
  onstop = null as (() => void) | null;
  onerror = null as ((event: Event) => void) | null;
  state: RecordingState = 'inactive';

  constructor(_stream: MediaStream, _options?: MediaRecorderOptions) {
    Object.assign(this, mockMediaRecorder);
  }

  start() {
    this.state = 'recording';
  }

  stop() {
    this.state = 'inactive';
    setTimeout(() => this.onstop?.(), 0);
  }

  static isTypeSupported(type: string): boolean {
    return type === 'audio/webm' || type === 'audio/mp4';
  }
}

// @ts-expect-error - mocking global
globalThis.MediaRecorder = MockMediaRecorder;

// Mock navigator.mediaDevices.getUserMedia
Object.defineProperty(navigator, 'mediaDevices', {
  value: {
    getUserMedia: vi.fn().mockResolvedValue({
      getTracks: () => [
        {
          stop: vi.fn(),
          kind: 'audio',
        },
      ],
    }),
  },
  writable: true,
});

// Mock Audio
class MockAudio {
  src = '';
  currentTime = 0;
  duration = 10;
  paused = true;

  private listeners: Record<string, EventListener[]> = {};

  play = vi.fn().mockResolvedValue(undefined);
  pause = vi.fn(() => {
    this.paused = true;
  });
  load = vi.fn();

  addEventListener(event: string, listener: EventListener) {
    if (!this.listeners[event]) {
      this.listeners[event] = [];
    }
    this.listeners[event].push(listener);

    // Auto-fire loadedmetadata for tests
    if (event === 'loadedmetadata') {
      setTimeout(() => listener(new Event('loadedmetadata')), 0);
    }
  }

  removeEventListener(event: string, listener: EventListener) {
    if (this.listeners[event]) {
      this.listeners[event] = this.listeners[event].filter(l => l !== listener);
    }
  }

  dispatchEvent(event: Event) {
    const eventListeners = this.listeners[event.type] || [];
    eventListeners.forEach(listener => listener(event));
    return true;
  }
}

// @ts-expect-error - mocking global
globalThis.Audio = MockAudio;

// Mock URL.createObjectURL and revokeObjectURL
globalThis.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
globalThis.URL.revokeObjectURL = vi.fn();

// Mock Element.scrollIntoView
Element.prototype.scrollIntoView = vi.fn();

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value;
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
    get length() {
      return Object.keys(store).length;
    },
    key: (index: number) => {
      const keys = Object.keys(store);
      return keys[index] || null;
    },
  };
})();

Object.defineProperty(globalThis, 'localStorage', {
  value: localStorageMock,
  writable: true,
});
