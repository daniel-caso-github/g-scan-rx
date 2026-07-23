import React, { useRef, useState } from "react";
import { C, HAND } from "../styles/tokens";
import type { MedState } from "../hooks/useMedState";
import { fieldBucket } from "../hooks/useMedState";

interface Props {
  meds: MedState[];
  focused: string | null;
  onFocus: (id: string | null) => void;
  imageUrl?: string;
}

const ZOOM_MIN = 0.5;
const ZOOM_MAX = 4;
const ZOOM_STEP = 0.25;

function ZoomIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8" />
      <line x1="21" y1="21" x2="16.65" y2="16.65" />
      <line x1="11" y1="8" x2="11" y2="14" />
      <line x1="8" y1="11" x2="14" y2="11" />
    </svg>
  );
}

const btnStyle: React.CSSProperties = {
  width: 32, height: 32, borderRadius: 7,
  background: "rgba(255,255,255,0.15)", border: "1px solid rgba(255,255,255,0.2)",
  color: "#fff", cursor: "pointer", fontSize: 18,
  display: "flex", alignItems: "center", justifyContent: "center",
};

export function PrescriptionImage({ meds, focused, onFocus, imageUrl }: Props) {
  const [zoomed, setZoomed] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const dragOrigin = useRef<{ x: number; y: number; sl: number; st: number } | null>(null);

  function openZoom() { setZoomLevel(1); setZoomed(true); }

  function handleWheel(e: React.WheelEvent) {
    if (!e.ctrlKey && !e.metaKey) return;
    e.preventDefault();
    setZoomLevel(z => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z - e.deltaY * 0.001)));
  }

  function changeZoom(delta: number) {
    setZoomLevel(z => Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, Math.round((z + delta) * 100) / 100)));
  }

  function handleMouseDown(e: React.MouseEvent) {
    if (!scrollRef.current) return;
    dragOrigin.current = {
      x: e.clientX, y: e.clientY,
      sl: scrollRef.current.scrollLeft,
      st: scrollRef.current.scrollTop,
    };
    setIsDragging(true);
    e.preventDefault();
  }

  function handleMouseMove(e: React.MouseEvent) {
    if (!dragOrigin.current || !scrollRef.current) return;
    scrollRef.current.scrollLeft = dragOrigin.current.sl - (e.clientX - dragOrigin.current.x);
    scrollRef.current.scrollTop  = dragOrigin.current.st - (e.clientY - dragOrigin.current.y);
  }

  function handleMouseUp() {
    dragOrigin.current = null;
    setIsDragging(false);
  }

  React.useEffect(() => {
    if (!zoomed) return;
    const onKey = (e: KeyboardEvent) => { if (e.key === "Escape") setZoomed(false); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [zoomed]);

  return (
    <>
      <div style={{
        flex: "0 0 42%", display: "flex", flexDirection: "column",
        padding: "20px 22px", borderRight: `1px solid ${C.border}`,
        background: "#f2f5f7", overflow: "hidden",
      }}>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 12 }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: C.muted }}>
            Imagen original · Original image
          </div>
          <div style={{ fontSize: 11.5, color: "#9aa7b0" }}>
            Pase el cursor sobre un campo · Hover a field
          </div>
        </div>

        <div style={{ flex: 1, display: "flex", alignItems: "center", justifyContent: "center", minHeight: 0 }}>
          <div style={{
            position: "relative", height: "100%", aspectRatio: "3/4",
            maxWidth: "100%",
            background: imageUrl ? "#fff" : "#fffdf8",
            backgroundImage: imageUrl
              ? `url(${imageUrl})`
              : "repeating-linear-gradient(#fffdf8,#fffdf8 33px,#f0ece1 33px,#f0ece1 34px)",
            backgroundSize: imageUrl ? "contain" : undefined,
            backgroundRepeat: "no-repeat",
            backgroundPosition: "center",
            borderRadius: 8,
            boxShadow: "0 8px 30px rgba(20,35,46,.13)",
            border: "1px solid #e6e0d2",
          }}>
            {!imageUrl && (
              <>
                <div style={{ position: "absolute", left: "6%", top: "3.5%", fontFamily: HAND, fontSize: 30, fontWeight: 700, color: C.red }}>Rx</div>
                <div style={{ position: "absolute", right: "6%", top: "4.5%", textAlign: "right", fontFamily: HAND, fontSize: 16, color: C.muted, lineHeight: 1.3 }}>
                  Clínica San Rafael<br />12 / 07 / 2026
                </div>
                <div style={{ position: "absolute", left: "6%", top: "15%", fontFamily: HAND, fontSize: 17, color: "#3a4a54" }}>
                  Paciente: ██████████
                </div>
                <div style={{ position: "absolute", left: "6%", top: "20.5%", right: "6%", borderBottom: "1.5px solid #d8d2c4" }} />
              </>
            )}

            {meds.map((med, mi) =>
              med.fields.map(f => {
                const id = `${mi}-${f.key}`;
                const isFocused = focused === id;
                const bucket = fieldBucket(f);
                const isAbst = bucket === "abstention";
                const clr = isAbst ? C.red : bucket === "uncertain" ? C.amber : C.green;
                const b = f.bbox;
                return (
                  <div
                    key={id}
                    onMouseEnter={() => onFocus(id)}
                    onMouseLeave={() => onFocus(null)}
                    style={{
                      position: "absolute",
                      left: `${b.x}%`, top: `${b.y}%`, width: `${b.w}%`, height: `${b.h}%`,
                      borderRadius: 7, display: "flex", alignItems: "center",
                      justifyContent: "center", boxSizing: "border-box",
                      transition: ".14s", cursor: "default", overflow: "hidden",
                      border: isAbst
                        ? `2px dashed ${C.red}`
                        : `${isFocused ? "2.5px" : "1.5px"} solid ${isFocused ? C.brand : clr}`,
                      background: isFocused ? `${C.brand}22` : isAbst ? C.redBg : "transparent",
                      boxShadow: isFocused ? `0 0 0 3px ${C.brand}33` : undefined,
                    }}
                  >
                    {isAbst ? (
                      <svg width="70%" height="46%" viewBox="0 0 120 24" preserveAspectRatio="none">
                        <path d="M3 12 q6 -11 12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0 t12 0"
                          fill="none" stroke={C.red} strokeWidth="3" strokeLinecap="round" opacity=".55"/>
                      </svg>
                    ) : (
                      <span style={{ fontFamily: HAND, fontSize: 21, color: "#26404e", transform: "rotate(-2deg)", whiteSpace: "nowrap" }}>
                        {f.hand}
                      </span>
                    )}
                  </div>
                );
              })
            )}

            {/* Zoom button — always visible */}
            <button
              onClick={openZoom}
              title="Ver imagen completa"
              style={{
                position: "absolute", bottom: 10, right: 10,
                width: 34, height: 34, borderRadius: 8,
                background: "rgba(255,255,255,0.92)",
                border: `1px solid ${C.border}`,
                boxShadow: "0 2px 8px rgba(20,35,46,.15)",
                cursor: "pointer", display: "flex", alignItems: "center",
                justifyContent: "center", color: C.muted,
                transition: ".14s",
              }}
              onMouseEnter={e => (e.currentTarget.style.background = "#fff")}
              onMouseLeave={e => (e.currentTarget.style.background = "rgba(255,255,255,0.92)")}
            >
              <ZoomIcon />
            </button>
          </div>
        </div>

        <div style={{ display: "flex", gap: 16, marginTop: 14, flexWrap: "wrap" }}>
          {[
            { bg: C.greenBg, bd: C.greenBd, dashed: false, label: "Legible" },
            { bg: C.amberBg, bd: C.amberBd, dashed: false, label: "Dudoso · Uncertain" },
            { bg: C.redBg,   bd: C.redBd,   dashed: true,  label: "No legible · Abstention" },
          ].map(({ bg, bd, dashed, label }) => (
            <div key={label} style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 11.5, color: C.muted }}>
              <span style={{
                width: 11, height: 11, borderRadius: 3,
                border: `1.5px ${dashed ? "dashed" : "solid"} ${bd}`,
                background: bg,
              }} />
              {label}
            </div>
          ))}
        </div>
      </div>

      {/* Zoom modal */}
      {zoomed && (
        <div
          onClick={() => setZoomed(false)}
          style={{
            position: "fixed", inset: 0, zIndex: 1000,
            background: "rgba(10,20,28,0.88)",
            display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
          }}
        >
          {/* Scrollable image area + X button */}
          <div onClick={e => e.stopPropagation()} style={{ position: "relative" }}>
            <div
              ref={scrollRef}
              onWheel={handleWheel}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              onMouseLeave={handleMouseUp}
              style={{
                overflow: "auto", maxWidth: "90vw", maxHeight: "82vh",
                borderRadius: 10,
                boxShadow: "0 24px 80px rgba(0,0,0,.6)",
                cursor: isDragging ? "grabbing" : "grab",
                userSelect: "none",
              }}
            >
              {imageUrl ? (
                <img
                  src={imageUrl}
                  alt="Receta ampliada"
                  style={{
                    display: "block",
                    transformOrigin: "top left",
                    transform: `scale(${zoomLevel})`,
                    width: "auto", height: "auto",
                    maxWidth: "none",
                    transition: "transform .1s",
                  }}
                />
              ) : (
                <div style={{ padding: 48, color: "#fff", fontSize: 16 }}>Sin imagen cargada</div>
              )}
            </div>

            {/* X close button — top-right corner */}
            <button
              onClick={() => setZoomed(false)}
              title="Cerrar (Esc)"
              style={{
                position: "absolute", top: 10, right: 10,
                width: 34, height: 34, borderRadius: 8,
                background: "rgba(0,0,0,0.55)", border: "1px solid rgba(255,255,255,0.2)",
                color: "#fff", cursor: "pointer", fontSize: 20, lineHeight: 1,
                display: "flex", alignItems: "center", justifyContent: "center",
                backdropFilter: "blur(4px)",
              }}
            >
              ×
            </button>
          </div>

          {/* Controls bar */}
          <div
            onClick={e => e.stopPropagation()}
            style={{
              display: "flex", alignItems: "center", gap: 10, marginTop: 16,
              background: "rgba(255,255,255,0.1)", borderRadius: 10,
              padding: "8px 16px", backdropFilter: "blur(6px)",
            }}
          >
            <button onClick={() => changeZoom(-ZOOM_STEP)} style={btnStyle}>−</button>
            <span style={{ color: "#fff", fontSize: 13, minWidth: 40, textAlign: "center" }}>
              {Math.round(zoomLevel * 100)}%
            </span>
            <button onClick={() => changeZoom(ZOOM_STEP)} style={btnStyle}>+</button>
            <div style={{ width: 1, height: 18, background: "rgba(255,255,255,0.25)", margin: "0 4px" }} />
            <button onClick={() => setZoomLevel(1)} style={{ ...btnStyle, fontSize: 11, padding: "4px 10px" }}>1:1</button>
          </div>

          <div style={{ color: "rgba(255,255,255,0.4)", fontSize: 11, marginTop: 8 }}>
            Rueda del mouse para zoom · Scroll para desplazar
          </div>
        </div>
      )}
    </>
  );
}
