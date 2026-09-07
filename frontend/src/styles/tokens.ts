export const C = {
  ink:     "#14232e",
  // muted/dim darkened to clear WCAG AA (4.5:1) against both `white` and `bg`
  // — the originals failed 4.46:1 and 2.9:1 respectively (verified live via
  // impeccable detect, /impeccable harden fix).
  muted:   "#5a6973",
  dim:     "#606c75",
  brand:   "#0d6d8a",
  brandDk: "#084d5c",
  brandBg: "#eef7f9",
  brandBd: "#cfe6ea",
  green:   "#1f9d57",
  greenBg: "#e7f6ed",
  greenBd: "#bfe6cd",
  amber:   "#b9770a",
  amberBg: "#fbf0d8",
  amberBd: "#ecdcbf",
  red:     "#cf3b3b",
  redBg:   "#fbe8e8",
  redBd:   "#f0cccc",
  border:  "#dce4ea",
  bg:      "#eaeef2",
  white:   "#ffffff",
} as const;

export const MONO = "'IBM Plex Mono', monospace";
export const HAND = "'Caveat', cursive";
