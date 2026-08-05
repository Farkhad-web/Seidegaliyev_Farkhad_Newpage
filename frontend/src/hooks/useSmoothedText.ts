import { useEffect, useRef, useState } from "react";

/**
 * Decouples on-screen text reveal from the raw SSE delta stream.
 *
 * Claude's token deltas arrive in bursty, uneven chunks — rendering them
 * directly makes the answer feel like it's stuttering. This ramps the
 * visible slice of `target` forward at a steady character rate instead, so
 * the reveal reads as smooth typing regardless of network/model jitter.
 * If the source falls too far behind (a burst of tokens all at once), the
 * catch-up rate speeds up rather than letting a visible lag build up.
 */
export function useSmoothedText(target: string, streaming: boolean, charsPerSecond = 220): string {
  const [visible, setVisible] = useState(target);
  const targetRef = useRef(target);
  const visibleLenRef = useRef(target.length);
  targetRef.current = target;

  useEffect(() => {
    if (!streaming) {
      visibleLenRef.current = target.length;
      setVisible(target);
      return;
    }

    let rafId: number;
    let lastTime = performance.now();

    const tick = (now: number) => {
      const dt = (now - lastTime) / 1000;
      lastTime = now;

      const current = targetRef.current;
      const remaining = current.length - visibleLenRef.current;
      if (remaining > 0) {
        // Catch up faster the further behind we are, so a sudden burst of
        // tokens doesn't leave the UI visibly trailing the real content.
        const rate = remaining > 200 ? charsPerSecond * 4 : charsPerSecond;
        const step = Math.max(1, Math.round(rate * dt));
        visibleLenRef.current = Math.min(current.length, visibleLenRef.current + step);
        setVisible(current.slice(0, visibleLenRef.current));
      }
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
    // Intentionally excludes `target`: the loop reads it via targetRef so a
    // new delta extends the animation instead of restarting it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streaming, charsPerSecond]);

  return streaming ? visible : target;
}
