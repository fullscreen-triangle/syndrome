/**
 * useMeasure -- report an element's content width, live.
 *
 * The output column is user-resizable, so charts cannot carry fixed
 * widths: they measure the space they are given and redraw when it
 * changes. Falls back to a sensible width where ResizeObserver is
 * unavailable.
 */

import { useCallback, useEffect, useRef, useState } from "react";

export default function useMeasure(fallback = 440) {
  const [width, setWidth] = useState(fallback);
  const nodeRef = useRef(null);
  const roRef = useRef(null);

  // A callback ref, not useRef + useEffect([]): the component this
  // measures returns different root elements for different states
  // (hint / error / charts), so the observed node changes across
  // renders and a mount-only effect would keep watching a detached one.
  const ref = useCallback((node) => {
    if (roRef.current) {
      roRef.current.disconnect();
      roRef.current = null;
    }
    nodeRef.current = node;
    if (!node) return;

    const read = () => {
      const w = node.clientWidth;
      if (w > 0) setWidth((prev) => (Math.abs(prev - w) > 0.5 ? w : prev));
    };
    read();

    if (typeof ResizeObserver === "undefined") {
      window.addEventListener("resize", read);
      roRef.current = { disconnect: () => window.removeEventListener("resize", read) };
      return;
    }
    const ro = new ResizeObserver(read);
    ro.observe(node);
    roRef.current = ro;
  }, []);

  useEffect(() => () => roRef.current?.disconnect(), []);

  return [ref, width];
}
