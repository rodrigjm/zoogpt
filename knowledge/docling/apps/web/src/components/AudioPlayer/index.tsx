import { useEffect, useRef } from 'react';
import { useAudioPlayer } from '../../hooks';

interface AudioPlayerProps {
  audioBlob: Blob;
  autoPlay?: boolean;
  onEnded?: () => void;
}

function formatTime(seconds: number): string {
  if (!isFinite(seconds)) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function AudioPlayer({
  audioBlob,
  autoPlay = false,
  onEnded,
}: AudioPlayerProps) {
  const { isPlaying, isLoading, currentTime, duration, error, play, pause, seek, reset } =
    useAudioPlayer();

  const hasLoadedRef = useRef(false);
  const audioBlobRef = useRef<Blob | null>(null);

  // Load audio when audioBlob changes
  useEffect(() => {
    if (audioBlob && audioBlob !== audioBlobRef.current) {
      // Reset previous audio state before loading new blob
      reset();
      audioBlobRef.current = audioBlob;
      hasLoadedRef.current = false;

      if (autoPlay) {
        play(audioBlob);
        hasLoadedRef.current = true;
      }
    }
  }, [audioBlob, autoPlay, play, reset]);

  // Call onEnded callback when playback ends
  useEffect(() => {
    if (!isPlaying && hasLoadedRef.current && currentTime === 0 && duration > 0) {
      onEnded?.();
    }
  }, [isPlaying, currentTime, duration, onEnded]);

  const handlePlayPause = () => {
    if (isPlaying) {
      pause();
    } else {
      // Always play with current blob - hook handles cleanup
      play(audioBlob);
      hasLoadedRef.current = true;
    }
  };

  const handleProgressClick = (e: React.MouseEvent<HTMLDivElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const percentage = clickX / rect.width;
    const newTime = percentage * duration;
    seek(newTime);
  };

  const progress = duration > 0 ? (currentTime / duration) * 100 : 0;

  return (
    <div className="bg-gray-800 rounded-lg p-4 flex items-center gap-4">
      {/* Play/Pause Button */}
      <button
        onClick={handlePlayPause}
        disabled={isLoading}
        className="text-white hover:text-leesburg-orange transition-colors disabled:opacity-50 disabled:cursor-not-allowed text-2xl"
        aria-label={isPlaying ? 'Pause' : 'Play'}
      >
        {isLoading ? '⏳' : isPlaying ? '⏸️' : '▶️'}
      </button>

      {/* Progress Bar */}
      <div className="flex-1 flex items-center gap-3">
        <div
          onClick={handleProgressClick}
          className="flex-1 h-2 bg-gray-700 rounded-full cursor-pointer relative overflow-hidden"
        >
          <div
            className="h-full bg-leesburg-orange rounded-full transition-all"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* Time Display */}
        <div className="text-white text-sm whitespace-nowrap font-mono">
          {formatTime(currentTime)} / {formatTime(duration)}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="text-red-400 text-sm">
          {error}
        </div>
      )}
    </div>
  );
}
