/**
 * Mobile audio unlock helper.
 *
 * iOS Safari (and some Android browsers) require HTMLAudioElement.play() to be
 * invoked synchronously inside a user-activation gesture. Our TTS pipeline
 * receives audio chunks over async network calls, so play() runs many turns
 * after the originating tap and is rejected with NotAllowedError.
 *
 * The fix: maintain a single shared <audio> element and "unlock" it once on
 * the first user gesture by calling play() on a tiny silent buffer. After
 * that, subsequent play() calls on the same element are allowed.
 */

// 0.05s of silent mono 16-bit WAV @ 44.1kHz, base64-encoded.
const SILENT_WAV_DATA_URI =
  'data:audio/wav;base64,UklGRiQAAABXQVZFZm10IBAAAAABAAEARKwAAIhYAQACABAAZGF0YQAAAAA=';

let sharedAudio: HTMLAudioElement | null = null;
let unlocked = false;
let listenerInstalled = false;

export function getSharedAudioElement(): HTMLAudioElement {
  if (!sharedAudio) {
    sharedAudio = new Audio();
    sharedAudio.preload = 'auto';
    // Some iOS versions require an inline-playback hint to avoid fullscreen.
    sharedAudio.setAttribute('playsinline', '');
    sharedAudio.setAttribute('webkit-playsinline', '');
  }
  return sharedAudio;
}

export function isAudioUnlocked(): boolean {
  return unlocked;
}

/**
 * Synchronously kick a silent buffer through the shared element. MUST be
 * called from a real user-gesture handler (pointerdown, click, keydown).
 * Idempotent — safe to call on every gesture.
 */
export function unlockAudio(): void {
  if (unlocked) return;
  const audio = getSharedAudioElement();
  try {
    audio.muted = true;
    audio.src = SILENT_WAV_DATA_URI;
    const result = audio.play();
    if (result && typeof result.then === 'function') {
      result
        .then(() => {
          audio.pause();
          audio.currentTime = 0;
          audio.muted = false;
          unlocked = true;
        })
        .catch(() => {
          audio.muted = false;
        });
    } else {
      audio.muted = false;
      unlocked = true;
    }
  } catch {
    // Browsers that throw synchronously will simply remain locked; the next
    // gesture gets another chance.
    audio.muted = false;
  }
}

/**
 * Install a one-shot global listener that unlocks audio on the first user
 * gesture anywhere on the page. Safe to call multiple times.
 */
export function installGlobalAudioUnlock(): void {
  if (listenerInstalled || typeof window === 'undefined') return;
  listenerInstalled = true;

  const handler = () => {
    unlockAudio();
    if (unlocked) {
      window.removeEventListener('pointerdown', handler, true);
      window.removeEventListener('keydown', handler, true);
      window.removeEventListener('touchstart', handler, true);
    }
  };

  window.addEventListener('pointerdown', handler, true);
  window.addEventListener('keydown', handler, true);
  window.addEventListener('touchstart', handler, true);
}

/** Test-only: reset module state between tests. */
export function __resetAudioUnlockForTests(): void {
  sharedAudio = null;
  unlocked = false;
  listenerInstalled = false;
}
