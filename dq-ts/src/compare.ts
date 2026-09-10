// Python 참조 구현(dq/reports)과 TypeScript 엔진 출력(output/reports)의 동등성 비교
//   1) summary.json: 규칙 단위 status / violations / rows_checked / note, 상위 집계
//   2) findings.csv: (rule_id, table, field, row_key, person_id, detail) 다중집합 비교
import fs from "node:fs";
import path from "node:path";
import { parseArgs } from "node:util";
import { getRoot } from "./load.js";
import { readCsv } from "./csv.js";
import { COHORTS } from "./verify.js";
import type { Summary } from "./types.js";

const SEP = "\u0001";

export interface CompareResult {
  run: string;
  rules_py: number; rules_ts: number;
  rule_diffs: string[];
  top_diffs: string[];
  findings_py: number; findings_ts: number;
  only_py: string[]; only_ts: string[];
}

function findingKeys(p: string): Map<string, number> {
  const t = readCsv(p);
  const m = new Map<string, number>();
  const cols = ["rule_id", "table", "field", "row_key", "person_id", "detail"].map((c) => t.cols.get(c) ?? []);
  for (let i = 0; i < t.n; i++) {
    const k = cols.map((c) => c[i]).join(SEP);
    m.set(k, (m.get(k) ?? 0) + 1);
  }
  return m;
}

export function compareRun(run: string, pyDir: string, tsDir: string): CompareResult {
  const py: Summary = JSON.parse(fs.readFileSync(path.join(pyDir, "summary.json"), "utf-8"));
  const ts: Summary = JSON.parse(fs.readFileSync(path.join(tsDir, "summary.json"), "utf-8"));
  const res: CompareResult = { run, rules_py: py.rules_total, rules_ts: ts.rules_total, rule_diffs: [], top_diffs: [], findings_py: 0, findings_ts: 0, only_py: [], only_ts: [] };
  for (const k of ["rules_total", "rules_failed", "rules_skipped", "rules_error", "violations_total", "violations_error", "violations_warning"] as const)
    if (py[k] !== ts[k]) res.top_diffs.push(`${k}: py=${py[k]} ts=${ts[k]}`);
  for (const [t, n] of Object.entries(py.tables)) if (ts.tables[t] !== n) res.top_diffs.push(`tables.${t}: py=${n} ts=${ts.tables[t]}`);
  const tsRules = new Map(ts.rules.map((r) => [r.rule_id, r]));
  for (const r of py.rules) {
    const o = tsRules.get(r.rule_id);
    if (!o) { res.rule_diffs.push(`${r.rule_id}: TS 에 없음`); continue; }
    if (r.status !== o.status || r.violations !== o.violations || r.rows_checked !== o.rows_checked || r.note !== o.note)
      res.rule_diffs.push(`${r.rule_id}: py=${r.status}/${r.violations}/${r.rows_checked}/${r.note} ts=${o.status}/${o.violations}/${o.rows_checked}/${o.note}`);
  }
  for (const r of ts.rules) if (!py.rules.some((p) => p.rule_id === r.rule_id)) res.rule_diffs.push(`${r.rule_id}: Python 에 없음`);
  const fp = findingKeys(path.join(pyDir, "findings.csv")), ft = findingKeys(path.join(tsDir, "findings.csv"));
  res.findings_py = [...fp.values()].reduce((a, b) => a + b, 0);
  res.findings_ts = [...ft.values()].reduce((a, b) => a + b, 0);
  for (const [k, n] of fp) { const d = n - (ft.get(k) ?? 0); if (d > 0) res.only_py.push(`${k.split(SEP).join(" | ")} x${d}`); }
  for (const [k, n] of ft) { const d = n - (fp.get(k) ?? 0); if (d > 0) res.only_ts.push(`${k.split(SEP).join(" | ")} x${d}`); }
  return res;
}

export function compareAll(pyRoot = path.join(getRoot(), "dq/reports"), tsRoot = "output/reports"): CompareResult[] {
  const out: CompareResult[] = [];
  for (const c of COHORTS) for (const kind of ["clean", "dirty"]) {
    const run = `${kind}_${c}`;
    if (!fs.existsSync(path.join(tsRoot, run, "summary.json"))) continue;
    out.push(compareRun(run, path.join(pyRoot, run), path.join(tsRoot, run)));
  }
  return out;
}

export function printCompare(results: CompareResult[], maxLines = 12): boolean {
  let ok = true;
  console.log("| 실행 | 규칙 py/ts | findings py/ts | 규칙 차이 | 집계 차이 | py만 | ts만 |");
  console.log("|---|---|---|---|---|---|---|");
  for (const r of results) {
    const same = !r.rule_diffs.length && !r.top_diffs.length && !r.only_py.length && !r.only_ts.length && r.rules_py === r.rules_ts;
    if (!same) ok = false;
    console.log(`| ${r.run} | ${r.rules_py}/${r.rules_ts} | ${r.findings_py}/${r.findings_ts} | ${r.rule_diffs.length} | ${r.top_diffs.length} | ${r.only_py.length} | ${r.only_ts.length} |`);
  }
  for (const r of results) {
    const lines = [...r.top_diffs.map((d) => `  집계 ${d}`), ...r.rule_diffs.map((d) => `  규칙 ${d}`),
      ...r.only_py.map((d) => `  py만 ${d}`), ...r.only_ts.map((d) => `  ts만 ${d}`)];
    if (lines.length) { console.log(`\n[${r.run}] 차이 ${lines.length}건`); for (const l of lines.slice(0, maxLines)) console.log(l); if (lines.length > maxLines) console.log(`  ... ${lines.length - maxLines}건 더`); }
  }
  return ok;
}

if (process.argv[1] && process.argv[1].endsWith("compare.ts")) {
  const { values } = parseArgs({ options: { max: { type: "string", default: "12" } } });
  const ok = printCompare(compareAll(), Number(values.max));
  console.log(ok ? "\n동등성: 모든 실행에서 Python 참조 구현과 일치" : "\n동등성: 차이 있음");
  process.exit(ok ? 0 : 1);
}
