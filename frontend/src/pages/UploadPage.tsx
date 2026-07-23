import { useRef } from "react";
import { C } from "../styles/tokens";

interface Props {
  onFile: (f: File) => void;
  onSample: () => void;
  error: string | null;
}

export function UploadPage({ onFile, onSample, error }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div style={{
      position: "absolute", inset: 0, display: "flex",
      alignItems: "center", justifyContent: "center", padding: 32,
    }}>
      <div style={{ width: 560, maxWidth: "100%" }}>
        <div style={{ textAlign: "center", marginBottom: 26 }}>
          <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: "-.3px" }}>
            Digitalizar receta manuscrita
          </div>
          <div style={{ fontSize: 15, color: C.muted, marginTop: 5 }}>
            Digitize a handwritten prescription
          </div>
        </div>

        <div
          onClick={() => inputRef.current?.click()}
          style={{
            display: "flex", flexDirection: "column", alignItems: "center",
            justifyContent: "center", gap: 16, padding: "52px 28px",
            background: C.white, border: `2px dashed #b9c8d1`, borderRadius: 16,
            cursor: "pointer", transition: ".15s",
          }}
          onMouseEnter={e => {
            (e.currentTarget as HTMLDivElement).style.borderColor = C.brand;
            (e.currentTarget as HTMLDivElement).style.background = "#f6fbfc";
          }}
          onMouseLeave={e => {
            (e.currentTarget as HTMLDivElement).style.borderColor = "#b9c8d1";
            (e.currentTarget as HTMLDivElement).style.background = C.white;
          }}
        >
          <div style={{
            width: 58, height: 58, borderRadius: 14, background: C.brandBg,
            display: "flex", alignItems: "center", justifyContent: "center",
          }}>
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none">
              <path d="M12 16V4m0 0l-4 4m4-4l4 4" stroke={C.brand} strokeWidth="1.9" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M4 15v3a2 2 0 002 2h12a2 2 0 002-2v-3" stroke={C.brand} strokeWidth="1.9" strokeLinecap="round"/>
            </svg>
          </div>
          <div style={{ textAlign: "center" }}>
            <div style={{ fontSize: 16, fontWeight: 600 }}>
              Arrastre una foto o haga clic para subir
            </div>
            <div style={{ fontSize: 13, color: C.dim, marginTop: 3 }}>
              Drag a photo or click to upload · JPEG / PNG
            </div>
          </div>
          <input
            ref={inputRef}
            type="file"
            accept="image/*"
            style={{ display: "none" }}
            onChange={e => e.target.files?.[0] && onFile(e.target.files[0])}
          />
        </div>

        <div style={{ display: "flex", justifyContent: "center", marginTop: 20 }}>
          <button
            onClick={onSample}
            style={{
              display: "inline-flex", alignItems: "center", gap: 9,
              padding: "13px 22px", borderRadius: 11, border: "none",
              background: C.brand, color: "#fff", fontSize: 14.5,
              fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
            }}
            onMouseEnter={e => (e.currentTarget.style.background = C.brandDk)}
            onMouseLeave={e => (e.currentTarget.style.background = C.brand)}
          >
            <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
              <rect x="4" y="3" width="16" height="18" rx="2" stroke="#fff" strokeWidth="1.7"/>
              <path d="M8 8h8M8 12h8M8 16h5" stroke="#7fd4dd" strokeWidth="1.7" strokeLinecap="round"/>
            </svg>
            Usar receta de ejemplo · Use sample prescription
          </button>
        </div>

        {error && (
          <div style={{
            display: "flex", alignItems: "flex-start", gap: 9, marginTop: 16,
            padding: "12px 16px", background: C.redBg, border: `1px solid ${C.redBd}`,
            borderRadius: 11,
          }}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flex: "0 0 auto", marginTop: 1 }}>
              <circle cx="12" cy="12" r="9" stroke={C.red} strokeWidth="1.8"/>
              <path d="M6 6l12 12" stroke={C.red} strokeWidth="1.8"/>
            </svg>
            <span style={{ fontSize: 12.5, color: "#a33", lineHeight: 1.45 }}>{error}</span>
          </div>
        )}

        <div style={{
          display: "flex", alignItems: "flex-start", gap: 9, marginTop: 26,
          padding: "13px 16px", background: "#fbf6ee",
          border: "1px solid #ecdcbf", borderRadius: 11,
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flex: "0 0 auto", marginTop: 1 }}>
            <path d="M12 3l9 16H3l9-16z" stroke="#b9770a" strokeWidth="1.7" strokeLinejoin="round"/>
            <path d="M12 10v4M12 16.5v.5" stroke="#b9770a" strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          <span style={{ fontSize: 12.5, color: "#8a6a2e", lineHeight: 1.45 }}>
            Las imágenes con datos personales identificables se rechazan automáticamente. ·{" "}
            Images containing identifiable personal data are rejected automatically.
          </span>
        </div>
      </div>
    </div>
  );
}
