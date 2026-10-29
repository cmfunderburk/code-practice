import { useRef, type PointerEvent } from 'react';

const LONG_PRESS_MS = 500;
const MOVE_TOLERANCE_PX = 10;
const SWIPE_MIN_PX = 40;

export type Zone = 'reveal' | 'hide';

interface GestureHandlers {
  /** `target` is the element tapped, so a tap on a line's gutter can flag it. */
  onTap: (zone: Zone, target: Element) => void;
  onSwipe: (direction: 'next' | 'previous') => void;
  onLongPress: () => void;
}

interface Press {
  id: number;
  x: number;
  y: number;
  timer: ReturnType<typeof setTimeout>;
  longPressed: boolean;
}

/**
 * Drill gestures, from reader-lite's page gestures: tap the left third to hide
 * a step and the rest to reveal one (mirrored when `swapped`), swipe for the
 * next or previous unit, long-press to reveal the rest of a block. Vertical
 * scrolling stays the browser's: it cancels the press (pointercancel).
 */
export function useDrillGestures({ onTap, onSwipe, onLongPress }: GestureHandlers, swapped: boolean) {
  const press = useRef<Press | null>(null);

  const cancel = () => {
    if (press.current) clearTimeout(press.current.timer);
    press.current = null;
  };

  return {
    onPointerDown(event: PointerEvent<HTMLElement>) {
      if (!event.isPrimary) return;
      cancel();
      const { clientX: x, clientY: y, pointerId: id } = event;
      const timer = setTimeout(() => {
        if (press.current?.id !== id) return;
        press.current.longPressed = true;
        onLongPress();
      }, LONG_PRESS_MS);
      press.current = { id, x, y, timer, longPressed: false };
    },
    onPointerMove(event: PointerEvent<HTMLElement>) {
      const current = press.current;
      if (!current || current.id !== event.pointerId) return;
      if (Math.hypot(event.clientX - current.x, event.clientY - current.y) > MOVE_TOLERANCE_PX) {
        clearTimeout(current.timer);
      }
    },
    onPointerUp(event: PointerEvent<HTMLElement>) {
      const current = press.current;
      if (!current || current.id !== event.pointerId) return;
      cancel();
      if (current.longPressed) return;

      const dx = event.clientX - current.x;
      const dy = event.clientY - current.y;
      if (Math.abs(dx) >= SWIPE_MIN_PX && Math.abs(dx) > Math.abs(dy)) {
        onSwipe(dx < 0 ? 'next' : 'previous');
        return;
      }
      if (Math.hypot(dx, dy) > MOVE_TOLERANCE_PX) return;

      const rect = event.currentTarget.getBoundingClientRect();
      const fraction = (event.clientX - rect.left) / rect.width;
      const left = fraction < 1 / 3;
      const right = fraction > 2 / 3;
      const hide = swapped ? right : left;
      onTap(hide ? 'hide' : 'reveal', event.target as Element);
    },
    onPointerCancel: cancel,
  };
}
