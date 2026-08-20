/**
 * Editor.jsx -- a textarea overlaid on a syntax-highlighted mirror.
 *
 * The highlighter calls the same `highlight()` the lexer exports, so
 * what is coloured is exactly what the parser will read. Error lines
 * are marked from the interpreter's reported line number.
 */

import React, { useLayoutEffect, useRef } from "react";
import { highlight } from "../cfc/lexer.js";

const TOKEN_COLOR = {
  keyword: "#569cd6",
  type: "#4ec9b0",
  constant: "#d19a66",
  string: "#ce9178",
  number: "#b5cea8",
  comment: "#6a9955",
  operator: "#d4d4d4",
  ident: "#9cdcfe",
  plain: "#d4d4d4",
};

const FONT = "13px/20px ui-monospace, 'Cascadia Code', 'Fira Code', Consolas, monospace";

export default function Editor({ value, onChange, errorLine, readOnly }) {
  const taRef = useRef(null);
  const preRef = useRef(null);
  const gutRef = useRef(null);

  const lines = value.split("\n");

  useLayoutEffect(() => {
    const ta = taRef.current;
    if (!ta) return;
    const sync = () => {
      if (preRef.current) {
        preRef.current.scrollTop = ta.scrollTop;
        preRef.current.scrollLeft = ta.scrollLeft;
      }
      if (gutRef.current) gutRef.current.scrollTop = ta.scrollTop;
    };
    ta.addEventListener("scroll", sync);
    return () => ta.removeEventListener("scroll", sync);
  }, []);

  const onKeyDown = (e) => {
    if (e.key === "Tab") {
      e.preventDefault();
      const ta = e.target;
      const { selectionStart: s, selectionEnd: en } = ta;
      const next = value.slice(0, s) + "  " + value.slice(en);
      onChange(next);
      requestAnimationFrame(() => { ta.selectionStart = ta.selectionEnd = s + 2; });
    }
  };

  const shared = {
    margin: 0,
    padding: "8px 12px",
    font: FONT,
    whiteSpace: "pre",
    overflowWrap: "normal",
    tabSize: 2,
  };

  return (
    /* overflow:hidden matters: the textarea is absolutely positioned and
       would otherwise paint past the column edge, covering the splitter
       and swallowing its mousedown. */
    <div style={{
      display: "flex", flex: 1, minHeight: 0, minWidth: 0,
      background: "#1e1e1e", overflow: "hidden",
    }}>
      {/* gutter */}
      <div
        ref={gutRef}
        style={{
          ...shared,
          padding: "8px 8px 8px 12px",
          textAlign: "right",
          color: "#5a5a5a",
          userSelect: "none",
          overflow: "hidden",
          minWidth: 46,
          background: "#1e1e1e",
          borderRight: "1px solid #2a2a2a",
        }}
      >
        {lines.map((_, i) => (
          <div
            key={i}
            style={{
              height: 20,
              color: errorLine === i + 1 ? "#f44747" : undefined,
              fontWeight: errorLine === i + 1 ? 700 : 400,
            }}
          >
            {i + 1}
          </div>
        ))}
      </div>

      {/* code surface */}
      <div style={{ position: "relative", flex: 1, minWidth: 0 }}>
        <pre
          ref={preRef}
          aria-hidden
          style={{
            ...shared,
            position: "absolute",
            inset: 0,
            overflow: "auto",
            pointerEvents: "none",
            color: "#d4d4d4",
          }}
        >
          {lines.map((ln, i) => (
            <div
              key={i}
              style={{
                height: 20,
                background: errorLine === i + 1 ? "rgba(244,71,71,0.13)" : undefined,
              }}
            >
              {highlight(ln).map((t, j) => (
                <span key={j} style={{ color: TOKEN_COLOR[t.cls] || "#d4d4d4" }}>
                  {t.text}
                </span>
              ))}
              {ln.length === 0 ? "​" : ""}
            </div>
          ))}
        </pre>

        <textarea
          ref={taRef}
          value={value}
          readOnly={readOnly}
          onChange={(e) => onChange(e.target.value)}
          onKeyDown={onKeyDown}
          spellCheck={false}
          style={{
            ...shared,
            position: "absolute",
            inset: 0,
            width: "100%",
            height: "100%",
            resize: "none",
            border: "none",
            outline: "none",
            background: "transparent",
            color: "transparent",
            caretColor: "#ffffff",
            overflow: "auto",
          }}
        />
      </div>
    </div>
  );
}
