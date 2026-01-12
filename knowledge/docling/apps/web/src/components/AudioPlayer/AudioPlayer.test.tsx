import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import AudioPlayer from './index';

// Mock useAudioPlayer hook
const mockPlay = vi.fn();
const mockPause = vi.fn();
const mockStop = vi.fn();
const mockSeek = vi.fn();

vi.mock('../../hooks', () => ({
  useAudioPlayer: () => ({
    isPlaying: false,
    isLoading: false,
    currentTime: 0,
    duration: 10,
    error: null,
    play: mockPlay,
    pause: mockPause,
    stop: mockStop,
    seek: mockSeek,
  }),
}));

describe('AudioPlayer', () => {
  const mockAudioBlob = new Blob(['test-audio'], { type: 'audio/wav' });

  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Task 3.4 Acceptance Criteria', () => {
    it('should display player when audioBlob is provided', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const playButton = screen.getByRole('button', { name: /play/i });
      expect(playButton).toBeInTheDocument();
    });

    it('should have play/pause button', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const playButton = screen.getByRole('button', { name: /play/i });
      expect(playButton).toBeInTheDocument();
    });

    it('should toggle play on click', async () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const playButton = screen.getByRole('button', { name: /play/i });
      fireEvent.click(playButton);

      await waitFor(() => {
        expect(mockPlay).toHaveBeenCalledWith(mockAudioBlob);
      });
    });

    it('should display progress bar', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      // Progress bar container with cursor-pointer
      const progressBar = document.querySelector('.cursor-pointer.bg-gray-700');
      expect(progressBar).toBeInTheDocument();
    });

    it('should display time in correct format', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      // Should show 0:00 / 0:10 format
      expect(screen.getByText(/0:00/)).toBeInTheDocument();
    });

    it('should have dark background styling', () => {
      const { container } = render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const playerDiv = container.firstChild as HTMLElement;
      expect(playerDiv.className).toContain('bg-gray-800');
    });

    it('should have rounded corners', () => {
      const { container } = render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const playerDiv = container.firstChild as HTMLElement;
      expect(playerDiv.className).toContain('rounded-lg');
    });

    it('should have proper padding', () => {
      const { container } = render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const playerDiv = container.firstChild as HTMLElement;
      expect(playerDiv.className).toContain('p-4');
    });
  });

  describe('Progress Bar', () => {
    it('should allow clicking on progress bar to seek', async () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const progressBar = document.querySelector('.cursor-pointer.bg-gray-700') as HTMLElement;

      // Simulate click on progress bar
      fireEvent.click(progressBar, {
        clientX: 100,
      });

      await waitFor(() => {
        expect(mockSeek).toHaveBeenCalled();
      });
    });

    it('should show orange progress fill', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const progressFill = document.querySelector('.bg-leesburg-orange');
      expect(progressFill).toBeInTheDocument();
    });
  });

  describe('Auto-play', () => {
    it('should call play when autoPlay is true', async () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} autoPlay={true} />);

      await waitFor(() => {
        expect(mockPlay).toHaveBeenCalledWith(mockAudioBlob);
      });
    });

    it('should not auto-play when autoPlay is false', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} autoPlay={false} />);

      // Play should not be called automatically
      expect(mockPlay).not.toHaveBeenCalled();
    });
  });

  describe('Loading State', () => {
    it('should have disabled styles applied via className when loading', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const button = screen.getByRole('button');
      // Button has disabled:opacity-50 and disabled:cursor-not-allowed classes
      // which apply styles when disabled
      expect(button.className).toContain('disabled:opacity-50');
      expect(button.className).toContain('disabled:cursor-not-allowed');
    });
  });

  describe('Time Display', () => {
    it('should format time correctly', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      // Time display should show formatted time
      const timeDisplay = screen.getByText(/\d+:\d{2}/);
      expect(timeDisplay).toBeInTheDocument();
    });

    it('should have monospace font for time', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const timeContainer = document.querySelector('.font-mono');
      expect(timeContainer).toBeInTheDocument();
    });
  });

  describe('Button States', () => {
    it('should show play icon when not playing', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const playButton = screen.getByRole('button', { name: /play/i });
      expect(playButton.textContent).toContain('▶️');
    });

    it('should have proper aria-label', () => {
      render(<AudioPlayer audioBlob={mockAudioBlob} />);

      const button = screen.getByRole('button');
      expect(button).toHaveAttribute('aria-label');
    });
  });

  describe('onEnded callback', () => {
    it('should accept onEnded prop', () => {
      const onEnded = vi.fn();
      render(<AudioPlayer audioBlob={mockAudioBlob} onEnded={onEnded} />);

      // Component should render without error
      expect(screen.getByRole('button')).toBeInTheDocument();
    });
  });
});
