// 메인 · preload · 렌더러가 공유하는 타입과 IPC 계약

export interface AppConfig {
  /** 명세(spec/)와 규칙(rules/)이 있는 디렉터리 */
  root: string;
  /** 검증 실행일 기본값 (null 이면 오늘) */
  defaultToday: string | null;
  /** 앱 데이터 위치 (읽기 전용 정보) */
  userData: string;
  packaged: boolean;
}

export interface CohortInfo { id: string; kor: string; tables: string[] }

export interface RuleInfo {
  id: string; name: string; category: string; subcategory: string;
  severity: string; table: string; fields: string; check: string;
  desc: string; scope: string; kind: "structural" | "semantic"; sql?: string;
}

// ------------------------------------------------------------------ 입력
/** 사용자가 넣은 파일 하나(CSV) 또는 엑셀 시트 하나 */
export interface SourceCandidate {
  id: string;
  kind: "csv" | "xlsx";
  path: string;
  sheet?: string;
  /** 표시 이름 (파일명 또는 파일명/시트명) */
  name: string;
  rows: number;
  columns: string[];
  /** 앞 20행 표본 (사전 점검용) */
  sample: string[][];
  encoding: string;
  sizeBytes: number;
  error?: string;
}

export interface InputIssue { level: "error" | "warn" | "info"; text: string }

export interface TableCheck {
  table: string;
  kor: string;
  /** 없으면 검증 자체가 무의미한 테이블 (PERSON, 질환 특화) */
  required: boolean;
  candidateId: string | null;
  auto: boolean;
  rows: number | null;
  missingColumns: string[];
  extraColumns: string[];
  aliases: string[];
  issues: InputIssue[];
}

export interface InputPlan {
  cohort: string;
  candidates: SourceCandidate[];
  mapping: Record<string, string>; // table → candidateId
  tables: TableCheck[];
  errors: number;
  warnings: number;
  /** 실행 가능 여부 (error 가 없음) */
  ok: boolean;
}

export interface PreviewData { columns: string[]; rows: string[][]; total: number }

export type TemplateKind = "csv" | "xlsx" | "spec" | "sample";

// ------------------------------------------------------------------ 실행
export interface RunRequest {
  cohort: string;
  candidates: SourceCandidate[];
  mapping: Record<string, string>;
  today?: string;
  label?: string;
}

export interface RunProgress { runId: string; stage: string; done: number; total: number; text: string; pct: number }

export interface RunRecord {
  run_id: string; cohort: string; cohort_kor: string; label: string; data_dir: string;
  run_date: string; created_at: string;
  rules_total: number; rules_failed: number; rules_skipped: number; rules_error: number;
  violations_total: number; violations_error: number; violations_warning: number;
  rows_total: number; tables: Record<string, number>;
}

export interface RuleResultRow {
  rule_id: string; name: string; category: string; subcategory: string; severity: string;
  table_name: string; fields: string; check_type: string; status: string;
  violations: number; rows_checked: number; note: string;
}

export interface FindingRow {
  seq: number; rule_id: string; rule_name: string; category: string; severity: string;
  table_name: string; field: string; row_key: string; person_id: string; detail: string;
}

export interface FindingsQuery {
  runId: string; ruleId?: string; table?: string; severity?: string; search?: string;
  offset: number; limit: number;
}
export interface FindingsPage { total: number; rows: FindingRow[] }

export interface RunDetail { run: RunRecord; rules: RuleResultRow[]; report: string }

// ------------------------------------------------------------------ 출력
export interface OutputFile {
  key: "report" | "findings" | "rules" | "submission" | "summary";
  name: string;
  label: string;
  desc: string;
  path: string;
  size: number;
  /** 병원 밖으로 보내도 되는 파일인지 */
  shareable: boolean;
}
export interface RunOutputs { dir: string; inputDir: string; files: OutputFile[] }

export interface CohortStatus extends RunRecord { error_rate: number }

export interface Dashboard {
  latestByCohort: CohortStatus[];
  byCheck: { check: string; label: string; count: number }[];
  bySeverity: { severity: string; count: number }[];
  rulesCount: { structural: number; semantic: number; total: number };
  trend: { run_id: string; created_at: string; cohort: string; label: string; violations_error: number; violations_warning: number; rows_total: number; error_rate: number }[];
  totals: { rows: number; violations: number; error_rate: number; runs: number };
}

export interface Api {
  getConfig(): Promise<AppConfig>;
  setConfig(patch: Partial<Pick<AppConfig, "root" | "defaultToday">>): Promise<AppConfig>;
  listCohorts(): Promise<CohortInfo[]>;
  listRules(): Promise<RuleInfo[]>;
  chooseDirectory(title?: string): Promise<string | null>;
  chooseFiles(): Promise<string[]>;
  /** 드래그 앤 드롭으로 받은 File 객체들의 실제 경로 */
  pathsForFiles(files: File[]): string[];
  inspectInput(cohort: string, paths: string[], existing?: SourceCandidate[]): Promise<InputPlan>;
  checkInput(cohort: string, candidates: SourceCandidate[], mapping: Record<string, string>): Promise<InputPlan>;
  previewSource(candidate: SourceCandidate): Promise<PreviewData>;
  exportTemplate(cohort: string, kind: TemplateKind): Promise<string | null>;
  runValidation(req: RunRequest): Promise<RunRecord>;
  onProgress(cb: (p: RunProgress) => void): () => void;
  listRuns(): Promise<RunRecord[]>;
  getRun(runId: string): Promise<RunDetail>;
  getRunOutputs(runId: string): Promise<RunOutputs>;
  getFindings(q: FindingsQuery): Promise<FindingsPage>;
  exportFile(runId: string, key: OutputFile["key"]): Promise<string | null>;
  exportBundle(runId: string): Promise<string | null>;
  deleteRun(runId: string): Promise<void>;
  getDashboard(): Promise<Dashboard>;
  openPath(p: string): Promise<void>;
  onNav(cb: (page: string) => void): () => void;
  /** 자동 점검 모드에서 메인이 넣어 주는 입력 계획 (화면 캡처용) */
  onSmokePlan(cb: (plan: InputPlan) => void): () => void;
}
