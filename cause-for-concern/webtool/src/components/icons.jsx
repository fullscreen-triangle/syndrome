import React from "react";

const s = (p) => ({ width: p, height: p, viewBox: "0 0 20 20", fill: "none" });

export const FilesIcon = ({ size = 20, c = "#aaa" }) => (
  <svg {...s(size)}><path d="M4 2h7l4 4v12H4V2z" stroke={c} strokeWidth="1.3" />
    <path d="M11 2v4h4" stroke={c} strokeWidth="1.3" /></svg>
);

export const LabIcon = ({ size = 20, c = "#aaa" }) => (
  <svg {...s(size)}><path d="M8 2v6L3.5 16a1.4 1.4 0 001.2 2h10.6a1.4 1.4 0 001.2-2L12 8V2"
    stroke={c} strokeWidth="1.3" strokeLinejoin="round" />
    <path d="M7 2h6M6.6 12h6.8" stroke={c} strokeWidth="1.3" /></svg>
);

export const BookIcon = ({ size = 20, c = "#aaa" }) => (
  <svg {...s(size)}><path d="M3 3h5.5A2.5 2.5 0 0111 5.5V17a2 2 0 00-2-1.6H3V3z"
    stroke={c} strokeWidth="1.2" />
    <path d="M17 3h-5.5A2.5 2.5 0 009 5.5V17a2 2 0 012-1.6h6V3z"
      stroke={c} strokeWidth="1.2" /></svg>
);

export const RunIcon = ({ size = 13, c = "#fff" }) => (
  <svg width={size} height={size} viewBox="0 0 16 16" fill="none">
    <path d="M4 2.5l9.5 5.5L4 13.5v-11z" fill={c} /></svg>
);

export const FileGlyph = ({ c = "#7d7d7d" }) => (
  <svg width="13" height="13" viewBox="0 0 16 16" fill="none">
    <path d="M3.5 1.5h6l3 3v10h-9v-13z" stroke={c} strokeWidth="1.1" />
    <path d="M9.5 1.5v3h3" stroke={c} strokeWidth="1.1" /></svg>
);

export const ChevronIcon = ({ open, c = "#9a9a9a" }) => (
  <svg width="11" height="11" viewBox="0 0 16 16" fill="none"
    style={{ transform: open ? "rotate(90deg)" : "none", transition: "transform .12s" }}>
    <path d="M6 3.5L11 8l-5 4.5" stroke={c} strokeWidth="1.5"
      strokeLinecap="round" strokeLinejoin="round" /></svg>
);
