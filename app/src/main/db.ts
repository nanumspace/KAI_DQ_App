// 실행 이력 저장소 (DuckDB 파일). 실행마다 요약 · 규칙 결과 · 위반 행을 적재한다.
import fs from "node:fs";
import path from "node:path";
import { DuckDBInstance, DuckDBConnection, type DuckDBValue } from "@duckdb/node-api";
import type { Summary, RuleStat, RawTable } from "@engine/types.js";
import type { RunRecord, RuleResultRow, FindingRow, FindingsQuery, FindingsPage, Dashboard, CohortStatus } from "@shared/types";
import { checkLabel } from "@shared/labels";

let inst: DuckDBInstance | null = null;
let con: DuckDBConnection | null = null;

const SCHEMA = [
  `CREATE TABLE IF NOT EXISTS runs (
     run_id VARCHAR PRIMARY KEY, cohort VARCHAR, cohort_kor VARCHAR, label VARCHAR, data_dir VARCHAR,
     run_date VARCHAR, created_at VARCHAR,
     rules_total INTEGER, rules_failed INTEGER, rules_skipped INTEGER, rules_error INTEGER,
     violations_total INTEGER, violations_error INTEGER, violations_warning INTEGER,
     rows_total BIGINT, tables_json VARCHAR)`,
  `CREATE TABLE IF NOT EXISTS rule_results (
     run_id VARCHAR, rule_id VARCHAR, name VARCHAR, category VARCHAR, subcategory VARCHAR, severity VARCHAR,
     table_name VARCHAR, fields VARCHAR, check_type VARCHAR, status VARCHAR,
     violations INTEGER, rows_checked INTEGER, note VARCHAR)`,
  `CREATE TABLE IF NOT EXISTS findings (
     run_id VARCHAR, seq INTEGER, rule_id VARCHAR, rule_name VARCHAR, category VARCHAR, severity VARCHAR,
     table_name VARCHAR, field VARCHAR, row_key VARCHAR, person_id VARCHAR, detail VARCHAR)`,
];

export async function openDb(file: string): Promise<void> {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  inst = await DuckDBInstance.create(file);
  con = await inst.connect();
  for (const s of SCHEMA) await con.run(s);
}

export function closeDb(): void {
  con?.closeSync(); inst?.closeSync(); con = null; inst = null;
}

function c(): DuckDBConnection {
  if (!con) throw new Error("DB 가 열려 있지 않습니다");
  return con;
}

async function rows<T>(sql: string, params?: DuckDBValue[]): Promise<T[]> {
  const r = await c().runAndReadAll(sql, params);
  return r.getRowObjectsJson() as unknown as T[];
}

const NUM_FIELDS = ["rules_total", "rules_failed", "rules_skipped", "rules_error", "violations_total", "violations_error", "violations_warning", "rows_total"] as const;

/** DuckDB 의 BIGINT 는 JSON 변환 시 문자열이 될 수 있어 숫자 필드를 강제 변환한다. */
function toRun(r: Record<string, unknown>): RunRecord {
  const { tables_json, ...rest } = r as Record<string, unknown> & { tables_json: string };
  const out = { ...(rest as unknown as RunRecord), tables: JSON.parse(tables_json || "{}") };
  for (const k of NUM_FIELDS) out[k] = Number(out[k]);
  return out;
}

export interface InsertRunArgs {
  runId: string; cohort: string; cohortKor: string; label: string; dataDir: string; createdAt: string;
  summary: Summary; findings: RawTable;
}

export async function insertRun(a: InsertRunArgs): Promise<RunRecord> {
  const s = a.summary;
  const rowsTotal = Object.values(s.tables).reduce((x, y) => x + y, 0);
  await c().run(
    `INSERT INTO runs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)`,
    [a.runId, a.cohort, a.cohortKor, a.label, a.dataDir, s.run_date, a.createdAt,
     s.rules_total, s.rules_failed, s.rules_skipped, s.rules_error,
     s.violations_total, s.violations_error, s.violations_warning, rowsTotal, JSON.stringify(s.tables)]);
  const ra = await c().createAppender("rule_results");
  for (const r of s.rules as RuleStat[]) {
    ra.appendVarchar(a.runId); ra.appendVarchar(r.rule_id); ra.appendVarchar(r.name); ra.appendVarchar(r.category);
    ra.appendVarchar(r.subcategory); ra.appendVarchar(r.severity); ra.appendVarchar(r.table); ra.appendVarchar(r.fields);
    ra.appendVarchar(r.check); ra.appendVarchar(r.status); ra.appendInteger(r.violations); ra.appendInteger(r.rows_checked);
    ra.appendVarchar(r.note); ra.endRow();
  }
  ra.closeSync();
  const f = a.findings;
  const col = (n: string) => f.cols.get(n) ?? new Array<string>(f.n).fill("");
  const cols = ["rule_id", "rule_name", "category", "severity", "table", "field", "row_key", "person_id", "detail"].map(col);
  const fa = await c().createAppender("findings");
  for (let i = 0; i < f.n; i++) {
    fa.appendVarchar(a.runId); fa.appendInteger(i + 1);
    for (const cc of cols) fa.appendVarchar(cc[i]);
    fa.endRow();
  }
  fa.closeSync();
  return (await getRun(a.runId))!;
}

export async function listRuns(): Promise<RunRecord[]> {
  return (await rows<Record<string, unknown>>(`SELECT * FROM runs ORDER BY created_at DESC`)).map(toRun);
}

export async function getRun(runId: string): Promise<RunRecord | null> {
  const r = await rows<Record<string, unknown>>(`SELECT * FROM runs WHERE run_id = ?`, [runId]);
  return r.length ? toRun(r[0]) : null;
}

export async function getRuleResults(runId: string): Promise<RuleResultRow[]> {
  const rs = await rows<RuleResultRow>(`SELECT * FROM rule_results WHERE run_id = ? ORDER BY rowid`, [runId]);
  return rs.map((r) => ({ ...r, violations: Number(r.violations), rows_checked: Number(r.rows_checked) }));
}

export async function getFindings(q: FindingsQuery): Promise<FindingsPage> {
  const where: string[] = ["run_id = ?"]; const params: DuckDBValue[] = [q.runId];
  if (q.ruleId) { where.push("rule_id = ?"); params.push(q.ruleId); }
  if (q.table) { where.push("table_name = ?"); params.push(q.table); }
  if (q.severity) { where.push("severity = ?"); params.push(q.severity); }
  if (q.search) { where.push("(detail ILIKE ? OR rule_name ILIKE ? OR person_id = ? OR row_key = ?)"); params.push(`%${q.search}%`, `%${q.search}%`, q.search, q.search); }
  const w = where.join(" AND ");
  const total = (await rows<{ n: number }>(`SELECT count(*) AS n FROM findings WHERE ${w}`, params))[0].n;
  const page = await rows<FindingRow>(`SELECT * FROM findings WHERE ${w} ORDER BY seq LIMIT ? OFFSET ?`, [...params, q.limit, q.offset]);
  return { total: Number(total), rows: page.map((f) => ({ ...f, seq: Number(f.seq) })) };
}

export async function deleteRun(runId: string): Promise<void> {
  for (const t of ["findings", "rule_results", "runs"]) await c().run(`DELETE FROM ${t} WHERE run_id = ?`, [runId]);
}

export async function dashboard(rulesCount: Dashboard["rulesCount"]): Promise<Dashboard> {
  const all = (await rows<Record<string, unknown>>(`SELECT * FROM runs ORDER BY created_at`)).map(toRun);
  const latest = new Map<string, RunRecord>();
  for (const r of all) latest.set(r.cohort, r); // 시간순이므로 마지막이 최신
  const latestByCohort: CohortStatus[] = [...latest.values()].sort((a, b) => a.cohort.localeCompare(b.cohort))
    .map((r) => ({ ...r, error_rate: r.rows_total ? (r.violations_total / r.rows_total) * 100 : 0 }));
  const ids = latestByCohort.map((r) => r.run_id);
  let byCheck: Dashboard["byCheck"] = [], bySeverity: Dashboard["bySeverity"] = [];
  if (ids.length) {
    const ph = ids.map(() => "?").join(",");
    const bc = await rows<{ check_type: string; n: number }>(
      `SELECT check_type, sum(violations) AS n FROM rule_results WHERE run_id IN (${ph}) GROUP BY check_type HAVING sum(violations) > 0 ORDER BY n DESC`, ids);
    byCheck = bc.map((x) => ({ check: x.check_type, label: checkLabel(x.check_type), count: Number(x.n) }));
    const bs = await rows<{ severity: string; n: number }>(
      `SELECT severity, sum(violations) AS n FROM rule_results WHERE run_id IN (${ph}) GROUP BY severity`, ids);
    bySeverity = bs.map((x) => ({ severity: x.severity, count: Number(x.n) }));
  }
  const trend = all.slice(-40).map((r) => ({
    run_id: r.run_id, created_at: r.created_at, cohort: r.cohort, label: r.label,
    violations_error: r.violations_error, violations_warning: r.violations_warning, rows_total: r.rows_total,
    error_rate: r.rows_total ? (r.violations_total / r.rows_total) * 100 : 0,
  }));
  const rowsSum = latestByCohort.reduce((x, r) => x + r.rows_total, 0);
  const vioSum = latestByCohort.reduce((x, r) => x + r.violations_total, 0);
  return { latestByCohort, byCheck, bySeverity, rulesCount, trend,
    totals: { rows: rowsSum, violations: vioSum, error_rate: rowsSum ? (vioSum / rowsSum) * 100 : 0, runs: all.length } };
}
