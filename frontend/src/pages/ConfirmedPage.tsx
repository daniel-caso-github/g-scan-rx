import { C } from "../styles/tokens";
import type { MedState } from "../hooks/useMedState";

interface Props {
  result: "confirmed" | "rejected";
  meds: MedState[];
  onReset: () => void;
}

const VERDICTS = {
  verified:     { symbol: "✓", c: C.green,  bg: C.greenBg, bd: C.greenBd },
  uncertain:    { symbol: "⚠", c: C.amber,  bg: C.amberBg, bd: C.amberBd },
  no_encontrado:{ symbol: "✗", c: C.red,    bg: C.redBg,   bd: C.redBd   },
} as const;

export function ConfirmedPage({ result, meds, onReset }: Props) {
  const confirmed = result === "confirmed";
  const iconBg = confirmed ? C.green : C.red;

  return (
    <div style={{
      position: "absolute", inset: 0, display: "flex",
      alignItems: "center", justifyContent: "center", padding: 32,
    }}>
      <div style={{ width: 480, maxWidth: "100%", textAlign: "center" }}>
        <div style={{
          width: 76, height: 76, borderRadius: "50%", margin: "0 auto",
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          background: iconBg, animation: "gsr-pop .45s both",
        }}>
          {confirmed ? (
            <svg width="42" height="42" viewBox="0 0 24 24" fill="none">
              <path d="M5 12l4.5 4.5L19 7" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          ) : (
            <svg width="38" height="38" viewBox="0 0 24 24" fill="none">
              <path d="M6 6l12 12M18 6L6 18" stroke="#fff" strokeWidth="2.4" strokeLinecap="round"/>
            </svg>
          )}
        </div>

        <div style={{ fontSize: 24, fontWeight: 700, marginTop: 22 }}>
          {confirmed ? "Receta aceptada" : "Receta rechazada"}
        </div>
        <div style={{ fontSize: 15, color: C.muted, marginTop: 3 }}>
          {confirmed ? "Prescription accepted" : "Prescription rejected"}
        </div>
        <div style={{ fontSize: 13.5, color: C.dim, marginTop: 14, lineHeight: 1.5 }}>
          {confirmed
            ? "Todos los campos fueron confirmados por el revisor. El registro verificado se ha guardado. · All fields were confirmed by the reviewer. The verified record has been saved."
            : "La receta fue marcada como no válida y no se dispensará. · The prescription was flagged as invalid and will not be dispensed."}
        </div>

        <div style={{ marginTop: 26, display: "flex", flexDirection: "column", gap: 9, textAlign: "left" }}>
          {meds.map((med, i) => {
            const v = VERDICTS[med.verdict.status];
            const doseField = med.fields.find(f => f.key === "dose");
            return (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 11,
                padding: "12px 15px", background: C.white,
                border: `1px solid ${C.border}`, borderRadius: 11,
              }}>
                <span style={{
                  width: 26, height: 26, borderRadius: "50%",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 13, fontWeight: 700, color: "#fff", background: v.c, flex: "0 0 auto",
                }}>
                  {v.symbol}
                </span>
                <span style={{ fontWeight: 600, fontSize: 14.5, flex: 1 }}>
                  {med.fields.find(f => f.key === "drug")?.value || med.drugRaw}
                </span>
                <span style={{ fontFamily: "'IBM Plex Mono', monospace", fontSize: 12.5, color: C.muted }}>
                  {doseField?.value || "—"}
                </span>
              </div>
            );
          })}
        </div>

        <button
          onClick={onReset}
          style={{
            marginTop: 26, padding: "13px 24px", borderRadius: 11,
            border: "none", background: C.brand, color: "#fff",
            fontSize: 14.5, fontWeight: 600, cursor: "pointer", fontFamily: "inherit",
          }}
          onMouseEnter={e => (e.currentTarget.style.background = C.brandDk)}
          onMouseLeave={e => (e.currentTarget.style.background = C.brand)}
        >
          Nueva receta · New prescription
        </button>

        <div style={{
          display: "flex", alignItems: "flex-start", gap: 9, marginTop: 26,
          padding: "13px 16px", background: C.amberBg,
          border: `1px solid ${C.amberBd}`, borderRadius: 11, textAlign: "left",
        }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" style={{ flex: "0 0 auto", marginTop: 1 }}>
            <circle cx="12" cy="12" r="9" stroke={C.amber} strokeWidth="1.8"/>
            <path d="M12 8v5M12 16v.5" stroke={C.amber} strokeWidth="1.8" strokeLinecap="round"/>
          </svg>
          <span style={{ fontSize: 12.5, color: "#8a6a2e", lineHeight: 1.45 }}>
            Este resultado es de verificación asistida y no reemplaza la validación farmacéutica
            profesional. · This result comes from assisted verification and does not replace
            professional pharmaceutical validation.
          </span>
        </div>
      </div>
    </div>
  );
}
