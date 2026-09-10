// 교차 테이블 규칙. 명세 타입으로 변환한 테이블을 DuckDB 에 적재하고 SQL 규칙을 실행한다.
// 타입 변환은 참조 구현(pandas to_numeric / to_datetime, errors="coerce")과 같이 실패 시 NULL 이다.
import { DuckDBInstance, DuckDBConnection } from "@duckdb/node-api";
import type { RawTable, SemanticRule, Spec, Concepts, RuleStat } from "./types.js";
import { pyList, pySorted } from "./pyrepr.js";

const KCD_FIELD: Record<string, string> = {
  LUNG_CANCER: "lucn_diag_kncd", BREAST_CANCER: "brcn_diag_kncd", COLORECTAL_CANCER: "clcn_diag_kncd",
};

function q(name: string): string { return `"${name.replace(/"/g, '""')}"`; }

function castExpr(name: string, type: string): string {
  const c = q(name);
  switch (type) {
    case "integer": return `COALESCE(TRY_CAST(${c} AS BIGINT), TRY_CAST(TRY_CAST(${c} AS DOUBLE) AS BIGINT)) AS ${c}`;
    case "float": return `TRY_CAST(${c} AS DOUBLE) AS ${c}`;
    case "date": return `TRY_CAST(TRY_CAST(${c} AS TIMESTAMP) AS DATE) AS ${c}`;
    case "timestamp": return `TRY_CAST(${c} AS TIMESTAMP) AS ${c}`;
    default: return c;
  }
}

function sqlStr(s: string): string { return `'${s.replace(/'/g, "''")}'`; }

/** DuckDB 값 → 문자열 (person_id 는 정수화, NULL 은 null) */
function valStr(v: unknown): string | null {
  if (v === null || v === undefined) return null;
  if (typeof v === "bigint") return v.toString();
  if (typeof v === "number") return String(Number.isInteger(v) ? v : Math.trunc(v));
  return String(v);
}

export interface SemanticContext {
  cohort: string;
  todayIso: string;
  spec: Spec;
  concepts: Concepts;
  tablesInCohort: string[];
  raw: Map<string, RawTable>;
  diseaseTable: string;
  /** cohort_definition 경계의 YAML 원문 표기 (없으면 숫자 그대로) */
  cdText?: { female_min: string; female_max: string; age_min: string; age_max: string };
  onRule?: (i: number, n: number, ruleId: string) => void;
}

export interface SemanticSink {
  initStat(rule: SemanticRule, table: string): RuleStat;
  add(rule: { id: string; name: string; category: string; severity: string }, table: string, field: string, rowKey: string, personId: string | null, detail: string): void;
}

async function loadTable(con: DuckDBConnection, name: string, df: RawTable, spec: Spec): Promise<void> {
  // 명세에 있는 컬럼만, 명세 순서로 적재한다 (참조 구현의 typed() 와 같음)
  const fields = spec.tables[name].fields.filter((f) => df.cols.has(f.name));
  const rawName = `_raw_${name}`;
  await con.run(`CREATE TABLE ${q(rawName)} (${fields.map((f) => `${q(f.name)} VARCHAR`).join(", ")})`);
  if (fields.length && df.n) {
    const app = await con.createAppender(rawName);
    const cols = fields.map((f) => df.cols.get(f.name)!);
    for (let i = 0; i < df.n; i++) {
      for (let j = 0; j < cols.length; j++) {
        const v = cols[j][i];
        if (v === "") app.appendNull(); else app.appendVarchar(v);
      }
      app.endRow();
    }
    app.closeSync();
  }
  await con.run(`CREATE TABLE ${q(name)} AS SELECT ${fields.map((f) => castExpr(f.name, f.type)).join(", ")} FROM ${q(rawName)}`);
}

export async function runSemantic(ctx: SemanticContext, rules: SemanticRule[], sink: SemanticSink): Promise<void> {
  const inst = await DuckDBInstance.create(":memory:");
  const con = await inst.connect();
  try {
    for (const t of ctx.tablesInCohort) {
      const df = ctx.raw.get(t);
      if (df) await loadTable(con, t, df, ctx.spec);
    }
    // 보조 테이블
    const mc = Object.entries(ctx.concepts.measurements).map(([k, v]) =>
      `(${Number(k)}, ${sqlStr(v.name)}, ${Number(v.plausible[0])}, ${Number(v.plausible[1])})`);
    await con.run(`CREATE TABLE _MEASUREMENT_CONCEPTS (concept_id BIGINT, name VARCHAR, lo DOUBLE, hi DOUBLE)`);
    if (mc.length) await con.run(`INSERT INTO _MEASUREMENT_CONCEPTS VALUES ${mc.join(", ")}`);
    const ac = Object.entries(ctx.concepts.drugs).filter(([, v]) => v.category !== null && v.category !== undefined)
      .map(([k, v]) => `(${Number(k)}, ${sqlStr(v.name)})`);
    await con.run(`CREATE TABLE _ANTICANCER_DRUGS (concept_id BIGINT, name VARCHAR)`);
    if (ac.length) await con.run(`INSERT INTO _ANTICANCER_DRUGS VALUES ${ac.join(", ")}`);

    const cd = ctx.concepts.cohort_definition[ctx.cohort];
    const dtab = ctx.diseaseTable;
    const subst: Record<string, string> = {
      "{TODAY}": `DATE '${ctx.todayIso}'`,
      "{COHORT_CONDITION_IDS}": cd.condition_concept_ids.join(","),
      "{DISEASE}": dtab,
      "{DISEASE_PK}": ctx.spec.tables[dtab].pk,
      "{DISEASE_KCD}": KCD_FIELD[dtab] ?? "NULL",
      "{KCD_MATCH}": cd.kcd_prefix.map((p) => `kcd LIKE '${p}%'`).join(" OR "),
      "{FEMALE_MIN}": ctx.cdText?.female_min ?? String(cd.female_ratio.min), "{FEMALE_MAX}": ctx.cdText?.female_max ?? String(cd.female_ratio.max),
      "{AGE_MIN}": ctx.cdText?.age_min ?? String(cd.age_at_index.median_min), "{AGE_MAX}": ctx.cdText?.age_max ?? String(cd.age_at_index.median_max),
    };
    const present = new Set(ctx.raw.keys());
    let idx = 0;
    for (const rule of rules) {
      idx += 1;
      ctx.onRule?.(idx, rules.length, rule.id);
      if (rule.scope !== "all" && !rule.scope.includes(ctx.cohort)) continue;
      const req = rule.requires;
      const st = sink.initStat(rule, req.length ? pySorted(req).join(",") : dtab);
      const missing = req.filter((t) => !present.has(t));
      if (missing.length || !present.has(dtab)) {
        st.status = "skipped"; st.note = `필요 테이블 없음: ${pyList(pySorted(missing))}`; continue;
      }
      let sql = rule.sql;
      for (const [k, v] of Object.entries(subst)) sql = sql.split(k).join(v);
      let rows: unknown[][];
      try {
        const reader = await con.runAndReadAll(sql);
        rows = reader.getRows();
      } catch (e) {
        st.status = "error"; st.note = `SQL 오류: ${String((e as Error).message ?? e).slice(0, 200)}`; continue;
      }
      for (const [personId, rowKey, detail] of rows) {
        const rk = valStr(rowKey);
        sink.add(rule, st.table, "", rk === null ? "None" : rk, valStr(personId), valStr(detail) ?? "");
      }
      if (st.violations > 0) st.status = "fail";
    }
  } finally {
    con.closeSync();
    inst.closeSync();
  }
}
