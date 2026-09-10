// 명세 · 규칙 · 결과 타입

export type FieldType = "integer" | "float" | "varchar" | "text" | "date" | "timestamp";

export interface SpecField {
  name: string;
  type: FieldType;
  required: boolean;
  [k: string]: unknown;
}

export interface SpecTable {
  name: string;
  kor: string;
  category: "core" | "disease" | string;
  pk: string;
  fields: SpecField[];
}

export interface Spec {
  tables: Record<string, SpecTable>;
}

export interface StructuralRule {
  id: string;
  name: string;
  category: string;
  subcategory?: string;
  table: string;
  fields: string[];
  severity: "error" | "warning";
  check: string;
  params: Record<string, any>;
  desc?: string;
  scope: "all" | string[];
  /** YAML 원문에서 가져온 range 경계 표기 (Python repr 과 일치시키기 위함) */
  paramText?: { min?: string; max?: string };
}

export interface SemanticRule {
  id: string;
  name: string;
  category: string;
  subcategory?: string;
  severity: "error" | "warning";
  scope: "all" | string[];
  requires: string[];
  desc?: string;
  sql: string;
}

export interface Finding {
  rule_id: string;
  rule_name: string;
  category: string;
  severity: string;
  table: string;
  field: string;
  row_key: string;
  person_id: string;
  detail: string;
}

export interface RuleStat {
  rule_id: string;
  name: string;
  category: string;
  subcategory: string;
  severity: string;
  table: string;
  fields: string;
  check: string;
  status: "pass" | "fail" | "skipped" | "error";
  violations: number;
  rows_checked: number;
  note: string;
}

export interface Summary {
  cohort: string;
  run_date: string;
  tables: Record<string, number>;
  rules_total: number;
  rules_failed: number;
  rules_skipped: number;
  rules_error: number;
  violations_total: number;
  violations_error: number;
  violations_warning: number;
  by_category: Record<string, { rules: number; failed: number; violations: number }>;
  rules: RuleStat[];
}

/** 열 지향 문자열 테이블. 값은 CSV 원문 그대로이며 NULL 은 빈 문자열이다. */
export interface RawTable {
  columns: string[];
  cols: Map<string, string[]>;
  n: number;
}

export interface CohortDefinition {
  condition_concept_ids: number[];
  kcd_prefix: string[];
  age_at_index: { median_min: number; median_max: number };
  female_ratio: { min: number; max: number };
}

export interface Concepts {
  cohort_definition: Record<string, CohortDefinition>;
  measurements: Record<string, { name: string; plausible: [number, number]; [k: string]: unknown }>;
  drugs: Record<string, { name: string; category?: number | null; [k: string]: unknown }>;
  [k: string]: unknown;
}
