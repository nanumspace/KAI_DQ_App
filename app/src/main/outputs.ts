// 출력물: 실행 폴더의 파일 5종 정의, 규칙별 결과 CSV 와 중앙 제출용 집계 생성, 묶음 내보내기
import fs from "node:fs";
import path from "node:path";
import { writeCsv } from "@engine/csv.js";
import type { Summary, RuleStat } from "@engine/types.js";
import type { OutputFile, RunOutputs } from "@shared/types";
import { checkLabel } from "@shared/labels";

export const APP_VERSION = "0.1.0";

const FILES: Omit<OutputFile, "path" | "size">[] = [
  { key: "report", name: "report.md", label: "검증 보고서", desc: "요약, 분류별 집계, 실패 규칙과 예시. 사람이 읽는 결과.", shareable: true },
  { key: "findings", name: "findings.csv", label: "위반 행 목록 (CSV)", desc: "규칙, 테이블, 행 키, 환자 ID, 상세. 병원 내부에서 데이터를 고칠 때 씁니다.", shareable: false },
  { key: "rules", name: "rule_results.csv", label: "규칙별 결과 (CSV)", desc: "규칙 전체의 통과·실패·건너뜀과 위반 수, 검사 행 수.", shareable: true },
  { key: "submission", name: "submission.json", label: "중앙 제출용 집계", desc: "환자 단위 정보를 뺀 규칙별 건수와 테이블 행 수. 병원 밖으로 보내는 유일한 파일.", shareable: true },
  { key: "summary", name: "summary.json", label: "실행 요약 (JSON)", desc: "엔진의 규칙 단위 원본 요약. 프로그램 간 비교용.", shareable: true },
];

/** 엔진 출력(report/findings/summary) 위에 rule_results.csv 와 submission.json 을 더한다 */
export function writeExtraOutputs(runDir: string, summary: Summary, meta: { cohortKor: string; label: string; runId: string }): void {
  const rules = summary.rules as RuleStat[];
  writeCsv(path.join(runDir, "rule_results.csv"),
    ["rule_id", "name", "category", "subcategory", "severity", "check", "table", "fields", "status", "violations", "rows_checked", "note"],
    rules.map((r) => ({ ...r })));
  const byCheck = new Map<string, { rules: number; failed: number; violations: number }>();
  for (const r of rules) {
    const b = byCheck.get(r.check) ?? { rules: 0, failed: 0, violations: 0 };
    b.rules++; if (r.status === "fail") b.failed++; b.violations += r.violations; byCheck.set(r.check, b);
  }
  const submission = {
    schema: "kai-dq-submission/1",
    app_version: APP_VERSION,
    run_id: meta.runId, cohort: summary.cohort, cohort_kor: meta.cohortKor, label: meta.label,
    run_date: summary.run_date, generated_at: new Date().toISOString(),
    tables: summary.tables,
    rows_total: Object.values(summary.tables).reduce((a, b) => a + b, 0),
    rules: { total: summary.rules_total, failed: summary.rules_failed, skipped: summary.rules_skipped, error: summary.rules_error },
    violations: { total: summary.violations_total, error: summary.violations_error, warning: summary.violations_warning },
    by_category: summary.by_category,
    by_check: [...byCheck.entries()].map(([check, b]) => ({ check, label: checkLabel(check), ...b })),
    by_rule: rules.map((r) => ({ rule_id: r.rule_id, name: r.name, category: r.category, severity: r.severity, check: r.check, table: r.table, status: r.status, violations: r.violations, rows_checked: r.rows_checked })),
    note: "환자 단위 정보(person_id, row_key, detail)는 포함하지 않습니다.",
  };
  fs.writeFileSync(path.join(runDir, "submission.json"), JSON.stringify(submission, null, 1), "utf-8");
}

export function runOutputs(runDir: string): RunOutputs {
  const files: OutputFile[] = FILES.map((f) => {
    const p = path.join(runDir, f.name);
    return { ...f, path: p, size: fs.existsSync(p) ? fs.statSync(p).size : 0 };
  });
  return { dir: runDir, inputDir: path.join(runDir, "input"), files };
}

/** 출력물 5종을 대상 폴더 아래 <실행 ID>/ 로 복사한다 */
export function exportBundle(runDir: string, runId: string, destRoot: string): string {
  const dest = path.join(destRoot, runId);
  fs.mkdirSync(dest, { recursive: true });
  for (const f of runOutputs(runDir).files) if (f.size > 0) fs.copyFileSync(f.path, path.join(dest, f.name));
  fs.writeFileSync(path.join(dest, "README.txt"), [
    `K-AI 코호트 데이터 품질검증 결과 · ${runId}`, "",
    ...FILES.map((f) => `- ${f.name}: ${f.label}. ${f.desc}${f.shareable ? "" : " [외부 제출 금지]"}`), "",
    "중앙에 제출할 때는 submission.json 만 보냅니다. findings.csv 는 환자 단위 정보가 있어 병원 밖으로 내보내지 않습니다.", ""].join("\n"), "utf-8");
  return dest;
}
