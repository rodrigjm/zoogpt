// apps/web/src/components/chat/__tests__/VoiceOverlay.test.tsx
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import VoiceOverlay from '../VoiceOverlay';
import { useVoiceStore } from '../../../stores/voiceStore';

// Helper to set the voice store's mode for a test
function setVoiceMode(mode: 'idle' | 'recording' | 'processing' | 'playing') {
  useVoiceStore.setState({ mode });
}

describe('VoiceOverlay', () => {
  beforeEach(() => {
    useVoiceStore.getState().reset();
  });

  it('renders a "Tap to Stop" button while recording', () => {
    setVoiceMode('recording');
    render(<VoiceOverlay onStop={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByRole('button', { name: /stop recording/i })).toBeInTheDocument();
    expect(screen.getByText(/tap to stop/i)).toBeInTheDocument();
  });

  it('calls onStop when the center stop button is tapped', () => {
    setVoiceMode('recording');
    const onStop = vi.fn();
    render(<VoiceOverlay onStop={onStop} onCancel={vi.fn()} />);
    fireEvent.click(screen.getByRole('button', { name: /stop recording/i }));
    expect(onStop).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when the cancel pill is tapped', () => {
    setVoiceMode('recording');
    const onCancel = vi.fn();
    render(<VoiceOverlay onStop={vi.fn()} onCancel={onCancel} />);
    fireEvent.click(screen.getByRole('button', { name: /^cancel$/i }));
    expect(onCancel).toHaveBeenCalledTimes(1);
  });

  it('does NOT call onCancel when the backdrop is tapped', () => {
    setVoiceMode('recording');
    const onCancel = vi.fn();
    const { container } = render(<VoiceOverlay onStop={vi.fn()} onCancel={onCancel} />);
    // The backdrop is the outermost div with the fixed inset-0 class
    const backdrop = container.querySelector('div.fixed.inset-0');
    expect(backdrop).not.toBeNull();
    fireEvent.click(backdrop!);
    expect(onCancel).not.toHaveBeenCalled();
  });

  it('disables the stop button while processing and shows "Sending…"', () => {
    setVoiceMode('processing');
    render(<VoiceOverlay onStop={vi.fn()} onCancel={vi.fn()} />);
    const stopButton = screen.getByRole('button', { name: /processing/i });
    expect(stopButton).toBeDisabled();
    expect(screen.getByText(/sending/i)).toBeInTheDocument();
  });
});
