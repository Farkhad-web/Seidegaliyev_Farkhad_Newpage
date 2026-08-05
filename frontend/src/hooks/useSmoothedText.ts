import { useEffect, useRef, useState } from "react";

/**
 * Ramps the visible slice of `target` forward at a steady rate instead of
 * rendering SSE deltas as they arrive — raw deltas are bursty and make the
 * answer look like it's stuttering. Speeds up if it falls too far behind.
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
        // catch up faster the further behind we are
        const rate = remaining > 200 ? charsPerSecond * 4 : charsPerSecond;
        const step = Math.max(1, Math.round(rate * dt));
        visibleLenRef.current = Math.min(current.length, visibleLenRef.current + step);
        setVisible(current.slice(0, visibleLenRef.current));
      }
      rafId = requestAnimationFrame(tick);
    };

    rafId = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafId);
    // target excluded on purpose — read via targetRef so a new delta
    // extends the animation instead of restarting it
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streaming, charsPerSecond]);

  return streaming ? visible : target;
}
