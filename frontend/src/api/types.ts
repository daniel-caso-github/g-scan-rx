export type FieldStatus = "readable" | "uncertain" | "unreadable";
export type VerdictStatus = "verified" | "uncertain" | "no_encontrado";

export interface ExtractedField {
  value: string | null;
  confidence: number;
  status: FieldStatus;
  source_crop?: { bbox: [number, number, number, number] };
}

export interface NormalizedDose {
  amount: number;
  unit: string;
  route: string | null;
}

export interface VerificationVerdict {
  status: VerdictStatus;
  catalog_id: string | null;
  match_score: number | null;
  normalized_dose: NormalizedDose | null;
}

export interface ExtractedMedication {
  drug: ExtractedField;
  dose: ExtractedField;
  frequency: ExtractedField;
  duration: ExtractedField;
  route: ExtractedField;
}

export interface VerifiedMedication {
  drug: ExtractedField;
  dose: ExtractedField;
  verdict: VerificationVerdict;
}

export interface Prescription {
  id: string;
  status: string;
  image_hash: string;
  medications: ExtractedMedication[];
}

export interface VerifiedRecord {
  prescription_id: string;
  needs_review: boolean;
  overall_confidence: number;
  medications: VerifiedMedication[];
}

export interface ApiResponse<T> {
  data: T | null;
  error: { code: string; message: string } | null;
}
