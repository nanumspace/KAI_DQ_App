// 검출 성능 평가 (dq/verify.py 이식): clean 오탐, dirty 재현율(manifest 대비)
import fs from "node:fs";
import path from "node:path";
import { parseArgs } from "node:util";
import { getRoot } from "./load.js";
import { readCsv } from "./csv.js";
import type { Summary } from "./types.js";

export const COHORTS = ["LUNG_CANCER", "BREAST_CANCER", "COLORECTAL_CANCER", "MASLD", "DIABETES", "LYMPHOMA"];

interface Row { [k: string]: string }
function rows(p: string): Row[] {
  const t = readCsv(p);
  const out: Row[] = [];
  for (let i = 0; i < t.n; i++) { const r: Row = {}; for (const c of t.columns) r[c] = t.cols.get(c)![i]; out.push(r); }
  return out;
}

export interface Verification {
  cohort: string;
  clean: { rules: number; violations: number; failed_rules: number; false_positive_rate: number | null };
  dirty: { rules: number; violations: number; failed_rules: number };
  faults_total: number; faults_detected: number; recall: number | null;
  fault_types: number; fault_types_fully_detected: number;
  missed: Row[];
  by_type: { fault_type: string; n: number; detected: number; recall: number }[];
  by_category: { category: string; n: number; detected: number; recall: number }[];
  collateral_rules: string[];
}

export function verify(cohort: string, reportsDir: string, manifestPath?: string): Verification {
  const clean: Summary = JSON.parse(fs.readFileSync(path.join(reportsDir, `clean_${cohort}/summary.json`), "utf-8"));
  const dirty: Summary = JSON.parse(fs.readFileSync(path.join(reportsDir, `dirty_${cohort}/summary.json`), "utf-8"));
  const findings = rows(path.join(reportsDir, `dirty_${cohort}/findings.csv`));
  const manifest = rows(manifestPath ?? path.join(getRoot(), `synth/output/dirty/${cohort}/fault_manifest.csv`));

  const byRule = new Map<string, Row[]>();
  for (const f of findings) { const a = byRule.get(f.rule_id) ?? []; a.push(f); byRule.set(f.rule_id, a); }
  const results: Row[] = [];
  for (const m of manifest) {
    const rules = m.expected_rules.split("|").filter(Boolean);
    let hit: string | null = null;
    outer: for (const r of rules) {
      for (const f of byRule.get(r) ?? []) {
        const tableLevel = f.row_key === "" && f.person_id === "";
        if (tableLevel && f.table === m.table) { hit = r; break outer; }
        if (m.person_id && f.person_id === m.person_id) { hit = r; break outer; }
        if (m.pk && (f.row_key === m.pk || f.row_key.endsWith(":" + m.pk))) { hit = r; break outer; }
      }
    }
    results.push({ fault_id: m.fault_id, fault_type: m.fault_type, category: m.category, table: m.table, field: m.field,
      expected_rules: m.expected_rules, detected: hit ? "True" : "False", detected_by: hit ?? "" });
  }
  const group = (key: string) => {
    const g = new Map<string, { n: number; detected: number }>();
    for (const r of results) { const e = g.get(r[key]) ?? { n: 0, detected: 0 }; e.n++; if (r.detected === "True") e.detected++; g.set(r[key], e); }
    return [...g.entries()].sort(([a], [b]) => (a < b ? -1 : a > b ? 1 : 0))
      .map(([k, e]) => ({ [key]: k, n: e.n, detected: e.detected, recall: Math.round((e.detected / e.n) * 1000) / 1000 }));
  };
  const byType = group("fault_type") as Verification["by_type"];
  const byCat = group("category") as Verification["by_category"];
  const total = results.length, det = results.filter((r) => r.detected === "True").length;
  const expected = new Set(manifest.flatMap((m) => m.expected_rules.split("|").filter(Boolean)));
  const fired = new Set(findings.map((f) => f.rule_id));
  const collateral = [...fired].filter((r) => !expected.has(r)).sort();
  const out: Verification = {
    cohort,
    clean: { rules: clean.rules_total, violations: clean.violations_total, failed_rules: clean.rules_failed, false_positive_rate: clean.violations_total === 0 ? 0 : null },
    dirty: { rules: dirty.rules_total, violations: dirty.violations_total, failed_rules: dirty.rules_failed },
    faults_total: total, faults_detected: det, recall: total ? Math.round((det / total) * 10000) / 10000 : null,
    fault_types: byType.length, fault_types_fully_detected: byType.filter((t) => t.recall === 1).length,
    missed: results.filter((r) => r.detected !== "True"), by_type: byType, by_category: byCat, collateral_rules: collateral,
  };
  fs.writeFileSync(path.join(reportsDir, `verification_${cohort}.json`), JSON.stringify(out, null, 1), "utf-8");
  const L: string[] = [`# 검출 성능 검증: ${cohort}`, "",
    `- clean 데이터: 규칙 ${clean.rules_total}개 실행, 위반 ${clean.violations_total}건 (오탐)`,
    `- dirty 데이터: 주입 오류 ${total}건 중 ${det}건 검출, 재현율 ${out.recall}`,
    `- 오류 유형 ${byType.length}종 중 전부 검출 ${out.fault_types_fully_detected}종`,
    `- 주입 오류의 부수 효과로 함께 발화한 규칙: ${collateral.length ? collateral.join(", ") : "없음"}`, "",
    "| 오류 유형 | 분류 | 주입 | 검출 | 재현율 |", "|---|---|---|---|---|"];
  const catOf = new Map(results.map((r) => [r.fault_type, r.category]));
  for (const t of byType) L.push(`| ${t.fault_type} | ${catOf.get(t.fault_type)} | ${t.n} | ${t.detected} | ${t.recall} |`);
  if (out.missed.length) {
    L.push("", "## 미검출", "", "| fault_id | 유형 | 테이블 | 필드 | 기대 규칙 |", "|---|---|---|---|---|");
    for (const m of out.missed) L.push(`| ${m.fault_id} | ${m.fault_type} | ${m.table} | ${m.field} | ${m.expected_rules} |`);
  }
  fs.writeFileSync(path.join(reportsDir, `verification_${cohort}.md`), L.join("\n") + "\n", "utf-8");
  return out;
}

export function writeVerificationSummary(reportsDir: string, vs: Verification[]): void {
  const L = ["# 검출 성능 요약", "", "| 코호트 | 실행 규칙 | clean 오탐 | 주입 오류 | 검출 | 재현율 | 오류 유형 (전부 검출 / 전체) |", "|---|---|---|---|---|---|---|"];
  for (const v of vs) L.push(`| ${v.cohort} | ${v.dirty.rules} | ${v.clean.violations} | ${v.faults_total} | ${v.faults_detected} | ${v.recall?.toFixed(2)} | ${v.fault_types_fully_detected} / ${v.fault_types} |`);
  const tf = vs.reduce((a, v) => a + v.faults_total, 0), td = vs.reduce((a, v) => a + v.faults_detected, 0), fp = vs.reduce((a, v) => a + v.clean.violations, 0);
  L.push(`| **합계** | | **${fp}** | **${tf}** | **${td}** | **${tf ? (td / tf).toFixed(2) : "-"}** | |`);
  fs.writeFileSync(path.join(reportsDir, "verification_summary.md"), L.join("\n") + "\n", "utf-8");
  fs.writeFileSync(path.join(reportsDir, "verification_summary.json"), JSON.stringify(vs.map(({ missed, by_type, by_category, ...rest }) => rest), null, 1), "utf-8");
}

if (process.argv[1] && process.argv[1].endsWith("verify.ts")) {
  const { values } = parseArgs({ options: { cohort: { type: "string" }, all: { type: "boolean" }, reports: { type: "string", default: "output/reports" } } });
  const list = values.all ? COHORTS : values.cohort ? [values.cohort] : [];
  if (!list.length) { console.error("--cohort <COHORT> 또는 --all"); process.exit(2); }
  const vs = list.map((c) => verify(c, values.reports!));
  for (const v of vs) console.log(`[${v.cohort}] clean violations=${v.clean.violations} faults=${v.faults_total} detected=${v.faults_detected} recall=${v.recall}`);
  if (values.all) writeVerificationSummary(values.reports!, vs);
}
