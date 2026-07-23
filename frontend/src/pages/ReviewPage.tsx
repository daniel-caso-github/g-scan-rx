import { useState } from "react";
import { C, MONO } from "../styles/tokens";
import { PrescriptionImage } from "../components/PrescriptionImage";
import { MedicationCard } from "../components/MedicationCard";
import { fieldBucket, useMedState } from "../hooks/useMedState";
import type { MedState } from "../hooks/useMedState";

interface Props {
  imageUrl: string;
  initialMeds: MedState[];
  prescriptionId: string;
  overallConfidence: number;
  onConfirm: () => void;
  onReject: () => void;
}

export function ReviewPage({
  imageUrl, initialMeds, prescriptionId, overallConfidence, onConfirm, onReject,
}: Props) {
  const { meds, setField } = useMedState(initialMeds);
  const [focused, setFocused] = useState<string | null>(null);

  let abstentions = 0, uncertain = 0;
  meds.forEach(m => m.fields.forEach(f => {
    const b = fieldBucket(f);
    if (b === "abstention") abstentions++;
    if (b === "uncertain") uncertain++;
  }));
  const reviewCount = abstentions + uncertain;
  const canConfirm = abstentions === 0;
  const pct = Math.round(overallConfidence * 100);
  const barColor = pct >= 80 ? C.green : pct >= 60 ? C.amber : C.red;

  return (
    <div style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column" }}>
      {/* sub-header */}
      <div style={{
        flex: "0 0 auto", display: "flex", alignItems: "center", gap: 20,
        padding: "14px 26px", background: C.white, borderBottom: `1px solid ${C.border}`,
      }}>
        <div>
          <div style={{ fontSize: 17, fontWeight: 700 }}>Revisión de receta · Prescription review</div>
          <div style={{ fontSize: 12.5, color: C.dim, fontFamily: MONO }}>ID {prescriptionId}</div>
        </div>
        <div style={{ flex: 1 }} />
        {reviewCount > 0 && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "7px 14px", borderRadius: 999, background: C.amberBg, border: `1px solid ${C.amberBd}`,
          }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <path d="M12 3l9 16H3l9-16z" stroke={C.amber} strokeWidth="1.8" strokeLinejoin="round"/>
              <path d="M12 10v4M12 16.5v.5" stroke={C.amber} strokeWidth="1.9" strokeLinecap="round"/>
            </svg>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: "#8a6a2e" }}>
              Requiere revisión humana · Needs human review
            </span>
          </div>
        )}
        <div style={{ display: "flex", alignItems: "center", gap: 11, minWidth: 210 }}>
          <div style={{ textAlign: "right" }}>
            <div style={{ fontSize: 11, color: C.dim, fontWeight: 500, textTransform: "uppercase", letterSpacing: ".5px" }}>Confianza global</div>
            <div style={{ fontSize: 11, color: C.dim, fontWeight: 500, marginTop: -1 }}>Overall confidence</div>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, width: 110 }}>
            <div style={{ fontFamily: MONO, fontWeight: 600, fontSize: 15, textAlign: "right", color: barColor }}>
              {pct}%
            </div>
            <div style={{ height: 7, borderRadius: 4, background: "#e9eef1", overflow: "hidden" }}>
              <div style={{ height: "100%", width: `${pct}%`, background: barColor, borderRadius: 4 }} />
            </div>
          </div>
        </div>
      </div>

      {/* body */}
      <div style={{ flex: 1, display: "flex", overflow: "hidden" }}>
        <PrescriptionImage
          meds={meds}
          focused={focused}
          onFocus={setFocused}
          imageUrl={imageUrl || undefined}
        />
        <div
          className="gsr-scroll"
          style={{ flex: 1, overflowY: "auto", padding: "20px 22px", display: "flex", flexDirection: "column", gap: 16 }}
        >
          {meds.map((med, i) => (
            <MedicationCard
              key={i}
              med={med}
              index={i}
              focused={focused}
              onFocus={setFocused}
              onFieldChange={(key, val) => setField(i, key, val)}
            />
          ))}
          <div style={{ height: 4 }} />
        </div>
      </div>

      {/* bottom bar */}
      <div style={{
        flex: "0 0 auto", display: "flex", alignItems: "center", gap: 20,
        padding: "14px 26px", background: C.white, borderTop: `1px solid ${C.border}`,
        boxShadow: "0 -3px 16px rgba(20,35,46,.05)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 22 }}>
          <div>
            <div style={{ fontSize: 19, fontWeight: 700, lineHeight: 1 }}>{meds.length}</div>
            <div style={{ fontSize: 11.5, color: C.dim }}>medicamentos · medications</div>
          </div>
          <div style={{ width: 1, height: 34, background: "#e4eaee" }} />
          <div>
            <div style={{ fontSize: 19, fontWeight: 700, lineHeight: 1, color: reviewCount > 0 ? C.amber : C.green }}>
              {reviewCount}
            </div>
            <div style={{ fontSize: 11.5, color: C.dim }}>campos por revisar · fields to review</div>
          </div>
        </div>

        {abstentions > 0 && (
          <div style={{
            display: "flex", alignItems: "center", gap: 8,
            padding: "8px 13px", borderRadius: 9, background: C.redBg, border: `1px solid ${C.redBd}`,
          }}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke={C.red} strokeWidth="1.8"/>
              <path d="M6 6l12 12" stroke={C.red} strokeWidth="1.8"/>
            </svg>
            <span style={{ fontSize: 12.5, fontWeight: 600, color: "#a33" }}>
              {abstentions} abstención(es) sin resolver · unresolved abstention(s)
            </span>
          </div>
        )}

        <div style={{ flex: 1 }} />

        <button
          onClick={onReject}
          style={{
            padding: "12px 20px", borderRadius: 10,
            border: `1.5px solid #e0c4c4`, background: C.white,
            color: C.red, fontSize: 14, fontWeight: 600,
            cursor: "pointer", fontFamily: "inherit",
          }}
          onMouseEnter={e => (e.currentTarget.style.background = "#fbf3f3")}
          onMouseLeave={e => (e.currentTarget.style.background = C.white)}
        >
          Rechazar · Reject
        </button>

        <button
          onClick={() => canConfirm && onConfirm()}
          style={{
            display: "inline-flex", alignItems: "center", gap: 9,
            padding: "12px 22px", borderRadius: 10, border: "none",
            fontSize: 14, fontWeight: 700, fontFamily: "inherit", transition: ".15s",
            background: canConfirm ? C.green : "#e4eaee",
            color: canConfirm ? "#fff" : "#a3b0b8",
            cursor: canConfirm ? "pointer" : "not-allowed",
          }}
        >
          <svg width="17" height="17" viewBox="0 0 24 24" fill="none">
            <path d="M5 12l4.5 4.5L19 7" stroke="currentColor" strokeWidth="2.1" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          {canConfirm
            ? "Confirmar receta · Confirm prescription"
            : `Resuelva ${abstentions} abstención(es)`}
        </button>
      </div>
    </div>
  );
}
