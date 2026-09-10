// 화면 표시용 이름표. 규칙 검사 유형과 심각도를 사람 말로 바꾼다.

export const CHECK_LABELS: Record<string, string> = {
  not_null: "필수값 누락",
  type: "데이터 타입 불일치",
  range: "값 범위 초과",
  codelist: "코드 유효성 오류",
  pattern: "패턴 불일치",
  fk: "관계 무결성 오류",
  pk_unique: "키 중복·누락",
  not_future: "미래 날짜",
  group_anchor: "그룹 기준일 누락",
  person_invariant: "환자 불변 필드 불일치",
  must_be_null: "NULL 필수 위반",
  columns: "컬럼 구성 불일치",
  table_present: "테이블 누락",
  sql: "논리·교차 검증",
};

export function checkLabel(check: string): string {
  return CHECK_LABELS[check] ?? check;
}

export const CATEGORY_LABELS: Record<string, string> = {
  Conformance: "적합성",
  Completeness: "완전성",
  Plausibility: "타당성",
};

export interface SeverityInfo { key: string; label: string; short: string; color: string; guide: string }

/** 규칙 심각도 error/warning 을 화면의 오류(High)/경고(Medium)/정보(Low) 로 대응시킨다. */
export const SEVERITIES: SeverityInfo[] = [
  { key: "error", label: "오류 (High)", short: "오류", color: "#d64545", guide: "데이터 보완 또는 수정. 반드시 수정 후 제출." },
  { key: "warning", label: "경고 (Medium)", short: "경고", color: "#e8a33d", guide: "데이터 수정 권장. 분석 전 검토 필요." },
  { key: "info", label: "정보 (Low)", short: "정보", color: "#3a9d5d", guide: "분석에 영향 없음. 참고 사항." },
];

export function severityInfo(key: string): SeverityInfo {
  return SEVERITIES.find((s) => s.key === key) ?? SEVERITIES[2];
}

/** 오류율(%) 에 따른 상태 색. 우수 <1, 양호 1~2, 주의 2~5, 위험 ≥5 */
export function rateStatus(pct: number): { label: string; color: string } {
  if (pct < 1) return { label: "우수", color: "#3a9d5d" };
  if (pct < 2) return { label: "양호", color: "#9ec13a" };
  if (pct < 5) return { label: "주의", color: "#e8a33d" };
  return { label: "위험", color: "#d64545" };
}

/** 검사 유형별 조치 안내 */
export const CHECK_GUIDES: Record<string, string> = {
  not_null: "필수 항목이 비어 있습니다. 원천 시스템에서 값을 보완하거나, 사전의 필수 여부를 재확인합니다.",
  type: "값의 형식이 명세와 다릅니다. 날짜는 YYYY-MM-DD, 숫자는 숫자만 넣습니다.",
  range: "값이 타당 범위를 벗어났습니다. 단위 오류나 입력 오류인지 확인합니다.",
  codelist: "코드표에 없는 값입니다. 코드표를 확인하고 병원 코드는 매핑표로 변환합니다.",
  pattern: "값의 표기 형식이 규칙과 다릅니다. 병기·KCD 등 표준 표기를 확인합니다.",
  fk: "참조하는 행이 없습니다. 참조 테이블의 누락 행을 함께 제출합니다.",
  pk_unique: "기본키가 비었거나 중복됩니다. 행 식별자를 고유하게 부여합니다.",
  not_future: "검증일 이후 날짜입니다. 입력 오류인지 확인합니다.",
  group_anchor: "그룹 값이 있으나 기준 날짜가 없습니다. 이벤트 날짜를 채웁니다.",
  person_invariant: "환자 수준 항목이 같은 환자 안에서 다릅니다. 한 값으로 정리합니다.",
  must_be_null: "이 코호트에서는 비어 있어야 하는 항목입니다.",
  columns: "명세와 컬럼 구성이 다릅니다. 컬럼명과 순서를 명세에 맞춥니다.",
  table_present: "필요한 테이블 파일이 없습니다. 코호트 구성에 맞는 CSV 를 모두 제출합니다.",
  sql: "테이블 간 논리 불일치입니다. 상세 내용의 날짜·값 관계를 확인합니다.",
};
