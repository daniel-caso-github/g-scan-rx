import { useState } from "react";
import type { ExtractedMedication, VerifiedMedication, VerdictStatus } from "../api/types";

export interface MedField {
  key: string;
  value: string;
  confidence: number;
  status: "readable" | "uncertain" | "unreadable";
  edited: boolean;
  bbox: { x: number; y: number; w: number; h: number };
  hand: string;
}

export interface MedState {
  drugRaw: string;
  verdict: { status: VerdictStatus; catalog_id: string | null; match_score: number | null };
  fields: MedField[];
}

export type FieldBucket = "readable" | "uncertain" | "abstention" | "corrected" | "resolved";

export function fieldBucket(f: MedField): FieldBucket {
  const hasVal = f.value.trim() !== "";
  if (f.status === "unreadable") return hasVal ? "resolved" : "abstention";
  if (f.status === "uncertain")  return f.edited ? "corrected" : "uncertain";
  return "readable";
}

const SAMPLE: MedState[] = [
  {
    drugRaw: "Amoxicilina",
    verdict: { status: "verified", catalog_id: "cima-123456", match_score: 0.94 },
    fields: [
      { key: "drug",      value: "Amoxicilina", confidence: 0.92, status: "readable",   edited: false, bbox: {x:6,y:24,w:40,h:8},  hand: "Amoxicilina" },
      { key: "dose",      value: "500 mg",       confidence: 0.85, status: "readable",   edited: false, bbox: {x:50,y:24,w:22,h:8}, hand: "500mg" },
      { key: "frequency", value: "cada 8 h",     confidence: 0.79, status: "readable",   edited: false, bbox: {x:6,y:33,w:26,h:7},  hand: "c/8h" },
      { key: "duration",  value: "7 días",       confidence: 0.58, status: "uncertain",  edited: false, bbox: {x:36,y:33,w:22,h:7}, hand: "7 días" },
      { key: "route",     value: "oral",          confidence: 0.90, status: "readable",   edited: false, bbox: {x:62,y:33,w:16,h:7}, hand: "V.O." },
    ],
  },
  {
    drugRaw: "Ibuprofeno",
    verdict: { status: "uncertain", catalog_id: "cima-789012", match_score: 0.81 },
    fields: [
      { key: "drug",      value: "Ibuprofeno",  confidence: 0.88, status: "readable",   edited: false, bbox: {x:6,y:48,w:40,h:8},  hand: "Ibuprofeno" },
      { key: "dose",      value: "",            confidence: 0.12, status: "unreadable", edited: false, bbox: {x:50,y:48,w:22,h:8}, hand: "" },
      { key: "frequency", value: "cada 12 h",  confidence: 0.55, status: "uncertain",  edited: false, bbox: {x:6,y:57,w:26,h:7},  hand: "c/12h" },
      { key: "duration",  value: "5 días",      confidence: 0.80, status: "readable",   edited: false, bbox: {x:36,y:57,w:22,h:7}, hand: "5 días" },
      { key: "route",     value: "oral",         confidence: 0.85, status: "readable",   edited: false, bbox: {x:62,y:57,w:16,h:7}, hand: "V.O." },
    ],
  },
  {
    drugRaw: "Metamizol",
    verdict: { status: "no_encontrado", catalog_id: null, match_score: 0.38 },
    fields: [
      { key: "drug",      value: "Metamizol", confidence: 0.54, status: "uncertain",  edited: false, bbox: {x:6,y:72,w:40,h:8},  hand: "Metamizol" },
      { key: "dose",      value: "575 mg",    confidence: 0.70, status: "readable",   edited: false, bbox: {x:50,y:72,w:22,h:8}, hand: "575mg" },
      { key: "frequency", value: "",          confidence: 0.09, status: "unreadable", edited: false, bbox: {x:6,y:81,w:26,h:7},  hand: "" },
      { key: "duration",  value: "3 días",    confidence: 0.66, status: "readable",   edited: false, bbox: {x:36,y:81,w:22,h:7}, hand: "3 días" },
      { key: "route",     value: "oral",       confidence: 0.80, status: "readable",   edited: false, bbox: {x:62,y:81,w:16,h:7}, hand: "V.O." },
    ],
  },
];

export function fromApiMeds(
  extracted: ExtractedMedication[],
  verified: VerifiedMedication[] | undefined,
): MedState[] {
  return extracted.map((med, i) => {
    const v = verified?.[i];
    const toField = (key: keyof ExtractedMedication, idx: number): MedField => {
      const f = med[key] as { value: string | null; confidence: number; status: string };
      return {
        key,
        value: f.value ?? "",
        confidence: f.confidence,
        status: f.status as MedField["status"],
        edited: false,
        bbox: { x: 6 + (idx % 2) * 44, y: 24 + Math.floor(idx / 2) * 9, w: 36, h: 7 },
        hand: f.value ?? "",
      };
    };
    const KEYS: (keyof ExtractedMedication)[] = ["drug", "dose", "frequency", "duration", "route"];
    return {
      drugRaw: med.drug.value ?? "Desconocido",
      verdict: v?.verdict ?? { status: "uncertain" as VerdictStatus, catalog_id: null, match_score: 0 },
      fields: KEYS.map((k, idx) => toField(k, idx)),
    };
  });
}

export function useMedState(initial: MedState[]) {
  const [meds, setMeds] = useState<MedState[]>(initial);

  function setField(medIdx: number, fieldKey: string, value: string) {
    setMeds(prev =>
      prev.map((m, i) =>
        i !== medIdx ? m : {
          ...m,
          fields: m.fields.map(f =>
            f.key !== fieldKey ? f : { ...f, value, edited: true }
          ),
        }
      )
    );
  }

  return { meds, setMeds, setField };
}

export { SAMPLE };
