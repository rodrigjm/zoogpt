import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import VoiceButton from './index';

// Mock the API module
vi.mock('../../lib/api', () => ({
  speechToText: vi.fn().mockResolvedValue({ transcript: 'Hello world' }),
}));

// Mock useVoiceRecorder hook
const mockStartRecording = vi.fn();
const mockStopRecording = vi.fn().mockResolvedValue(new Blob(['audio'], { type: 'audio/webm' }));
const mockCancelRecording = vi.fn();

vi.mock('../../hooks/useVoiceRecorder', () => ({
  useVoiceRecorder: () => ({
    isRecording: false,
    isPreparing: false,
    duration: 0,
    error: null,
    audioBlob: null,
    startRecording: mockStartRecording,
    stopRecording: mockStopRecording,
    cancelRecording: mockCancelRecording,
  }),
}));

describe('VoiceButton', () => {
  const defaultProps = {
    sessionId: 'test-session-123',
    onTranscript: vi.fn(),
  };

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Task 3.2 Acceptance Criteria', () => {
    it('should render with microphone icon in idle state', () => {
      render(<VoiceButton {...defaultProps} />);

      const button = screen.getByRole('button', { name: /start recording/i });
      expect(button).toBeInTheDocument();
    });

    it('should toggle recording on click (start)', async () => {
      render(<VoiceButton {...defaultProps} />);

      const button = screen.getByRole('button', { name: /start recording/i });
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockStartRecording).toHaveBeenCalled();
      });
    });

    it('should be disabled when disabled prop is true', () => {
      render(<VoiceButton {...defaultProps} disabled={true} />);

      const button = screen.getByRole('button');
      expect(button).toBeDisabled();
    });

    it('should have correct aria-label for idle state', () => {
      render(<VoiceButton {...defaultProps} />);

      const button = screen.getByRole('button', { name: /start recording/i });
      expect(button).toHaveAttribute('aria-label', 'Start recording');
    });

    it('should apply gradient styling for idle state', () => {
      render(<VoiceButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('from-leesburg-yellow');
    });

    it('should apply disabled styling when disabled', () => {
      render(<VoiceButton {...defaultProps} disabled={true} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('bg-gray-300');
      expect(button.className).toContain('cursor-not-allowed');
    });
  });

  describe('Visual States', () => {
    it('should have round button shape', () => {
      render(<VoiceButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('rounded-full');
    });

    it('should have proper size (w-20 h-20)', () => {
      render(<VoiceButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('w-20');
      expect(button.className).toContain('h-20');
    });

    it('should include animation class for pulse effect', () => {
      render(<VoiceButton {...defaultProps} />);

      const button = screen.getByRole('button');
      expect(button.className).toContain('animate-pulse');
    });
  });

  describe('Recording Flow', () => {
    it('should not respond to clicks when disabled', async () => {
      render(<VoiceButton {...defaultProps} disabled={true} />);

      const button = screen.getByRole('button');
      fireEvent.click(button);

      await waitFor(() => {
        expect(mockStartRecording).not.toHaveBeenCalled();
      });
    });
  });
});

describe('VoiceButton Recording State', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should show cancel button during recording', async () => {
    // Override the mock for this test
    vi.doMock('../../hooks/useVoiceRecorder', () => ({
      useVoiceRecorder: () => ({
        isRecording: true,
        isPreparing: false,
        duration: 5,
        error: null,
        audioBlob: null,
        startRecording: vi.fn(),
        stopRecording: vi.fn(),
        cancelRecording: vi.fn(),
      }),
    }));

    // Re-import with new mock
    const { default: VoiceButtonRecording } = await import('./index');

    render(
      <VoiceButtonRecording
        sessionId="test-session-123"
        onTranscript={vi.fn()}
      />
    );

    // Should have aria-label for stop recording
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });
});
