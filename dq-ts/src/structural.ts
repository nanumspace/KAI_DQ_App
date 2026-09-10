// 구조 규칙 검사. 원본 문자열 위에서 동작한다 (타입 오류를 잡기 위해).
// 각 검사의 판정과 detail 문자열은 dq/engine.py 의 run_structural 과 같다.
import type { RawTable, StructuralRule, Finding, RuleStat, Spec } from "./types.js";
import { pyList, pySorted } from "./pyrepr.js";

export const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
export const TS_RE = /^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?$/;
export const INT_RE = /^[+-]?\d+$/;
export const FLOAT_RE = /^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$/;

function daysInMonth(y: number, m: number): number {
  return new Date(Date.UTC(y, m, 0)).getUTCDate();
}

/** 'YYYY-MM-DD' 가 실제 달력 날짜인지 (pandas to_datetime 이 NaT 를 내는 경우를 잡는다) */
export function validDate(s: string): boolean {
  if (!DATE_RE.test(s)) return false;
  const y = +s.slice(0, 4), m = +s.slice(5, 7), d = +s.slice(8, 10);
  return m >= 1 && m <= 12 && d >= 1 && d <= daysInMonth(y, m);
}

export function validTimestamp(s: string): boolean {
  const m = TS_RE.exec(s);
  if (!m) return false;
  if (!validDate(s.slice(0, 10))) return false;
  if (m[1]) {
    const hh = +s.slice(11, 13), mi = +s.slice(14, 16);
    const ss = m[2] ? +s.slice(17, 19) : 0;
    if (hh > 23 || mi > 59 || ss > 59) return false;
  }
  return true;
}

/** ISO 날짜/타임스탬프 문자열 → epoch ms (무효면 null). pandas to_datetime(errors="coerce") 대응 */
export function parseIsoDate(s: string): number | null {
  if (validDate(s)) return Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10));
  if (validTimestamp(s)) {
    const t = s.replace(" ", "T");
    const ms = Date.parse(t.length === 16 ? t + ":00Z" : t.endsWith("Z") ? t : t + "Z");
    return Number.isNaN(ms) ? null : ms;
  }
  return null;
}

/** pandas to_numeric(errors="coerce") 대응 */
export function parseNum(s: string): number | null {
  if (s === "" || !FLOAT_RE.test(s)) return null;
  const v = Number(s);
  return Number.isFinite(v) ? v : null;
}

export interface StructuralContext {
  cohort: string;
  today: Date; // UTC 자정
  spec: Spec;
  codelists: Map<string, Set<string>>;
  tablesInCohort: string[];
  raw: Map<string, RawTable>;
  aliasesApplied: Array<[table: string, from: string, to: string]>;
  /** 규칙 i/n 처리 후 호출 (진행률 표시용) */
  onRule?: (i: number, n: number, ruleId: string) => void;
}

export interface RuleSink {
  initStat(rule: StructuralRule, table: string): RuleStat;
  add(rule: { id: string; name: string; category: string; severity: string }, table: string, field: string, rowKey: string, personId: string | null, detail: string): void;
}

function keyColumns(df: RawTable, pk: string): { pkcol: string[]; pid: string[] } {
  const empty = () => new Array<string>(df.n).fill("");
  return { pkcol: df.cols.get(pk) ?? empty(), pid: df.cols.get("person_id") ?? empty() };
}

export function runStructural(ctx: StructuralContext, rules: StructuralRule[], sink: RuleSink): void {
  const todayMs = ctx.today.getTime();
  let idx = 0;
  for (const rule of rules) {
    idx += 1;
    if (ctx.onRule && (idx % 25 === 0 || idx === rules.length)) ctx.onRule(idx, rules.length, rule.id);
    const table = rule.table;
    if (!ctx.tablesInCohort.includes(table)) continue;
    if (rule.scope !== "all" && !rule.scope.includes(ctx.cohort)) continue;
    const st = sink.initStat(rule, table);
    const chk = rule.check;
    if (chk === "table_present") {
      if (!ctx.raw.has(table)) sink.add(rule, table, "", "", null, `${table}.csv 없음`);
      continue;
    }
    const df = ctx.raw.get(table);
    if (!df) { st.status = "skipped"; st.note = "테이블 없음"; continue; }
    st.rows_checked = df.n;
    const { pkcol, pid } = keyColumns(df, ctx.spec.tables[table].pk);
    const fields = rule.fields;
    const p = rule.params;
    if (chk === "columns") {
      const exp = new Set<string>(p.expected as string[]);
      const have = new Set(df.columns);
      for (const c of pySorted([...exp].filter((c) => !have.has(c)))) sink.add(rule, table, c, "", null, `컬럼 누락: ${c}`);
      for (const c of pySorted([...have].filter((c) => !exp.has(c)))) sink.add(rule, table, c, "", null, `명세에 없는 컬럼: ${c} (경고)`);
      for (const [t, a, b] of ctx.aliasesApplied) if (t === table) sink.add(rule, table, a, "", null, `별칭 컬럼 ${a} 를 ${b} 로 해석함 (경고)`);
      continue;
    }
    const missing = fields.filter((f) => !df.cols.has(f));
    if (missing.length && chk !== "group_anchor" && chk !== "person_invariant") {
      st.status = "skipped"; st.note = `컬럼 없음: ${pyList(missing)}`; continue;
    }
    const col = (f: string) => df.cols.get(f)!;

    if (chk === "pk_unique") {
      const f = fields[0]; const vals = col(f);
      for (let i = 0; i < df.n; i++) if (vals[i] === "") sink.add(rule, table, f, "", pid[i], "PK NULL");
      const count = new Map<string, number>();
      for (const v of vals) if (v !== "") count.set(v, (count.get(v) ?? 0) + 1);
      for (let i = 0; i < df.n; i++) {
        const v = vals[i];
        if (v !== "" && (count.get(v) ?? 0) > 1) sink.add(rule, table, f, v, pid[i], `PK 중복: ${v}`);
      }
    } else if (chk === "not_null") {
      const f = fields[0]; const vals = col(f);
      for (let i = 0; i < df.n; i++) if (vals[i] === "") sink.add(rule, table, f, pkcol[i], pid[i], `${f} NULL`);
    } else if (chk === "type") {
      const f = fields[0]; const ty = p.type as string; const vals = col(f);
      const ok: (v: string) => boolean =
        ty === "integer" ? (v) => INT_RE.test(v)
        : ty === "float" ? (v) => FLOAT_RE.test(v)
        : ty === "date" ? validDate
        : ty === "timestamp" ? validTimestamp
        : () => true;
      for (let i = 0; i < df.n; i++) {
        const v = vals[i];
        if (v !== "" && !ok(v)) sink.add(rule, table, f, pkcol[i], pid[i], `${f}='${v}' 은 ${ty} 아님`);
      }
    } else if (chk === "fk") {
      const f = fields[0]; const rt = p.ref_table as string; const rc = p.ref_field as string;
      if (!ctx.tablesInCohort.includes(rt)) { st.status = "skipped"; st.note = `참조 테이블 ${rt} 코호트에 없음`; continue; }
      const ref = ctx.raw.get(rt);
      if (!ref || !ref.cols.has(rc)) { st.status = "skipped"; st.note = `참조 테이블 ${rt} 없음`; continue; }
      const refset = new Set(ref.cols.get(rc)!.filter((v) => v !== ""));
      const vals = col(f);
      for (let i = 0; i < df.n; i++) {
        const v = vals[i];
        if (v !== "" && !refset.has(v)) sink.add(rule, table, f, pkcol[i], pid[i], `${f}=${v} 가 ${rt}.${rc} 에 없음`);
      }
    } else if (chk === "codelist") {
      const f = fields[0]; const name = p.codelist as string;
      const allowed = ctx.codelists.get(name) ?? new Set<string>();
      const vals = col(f);
      for (let i = 0; i < df.n; i++) {
        const v = vals[i];
        if (v !== "" && !allowed.has(v)) sink.add(rule, table, f, pkcol[i], pid[i], `${f}=${v} 코드표(${name}) 밖`);
      }
    } else if (chk === "range") {
      const f = fields[0]; const lo = p.min as number; const hi = p.max as number;
      const loTxt = rule.paramText?.min ?? String(lo); const hiTxt = rule.paramText?.max ?? String(hi);
      const vals = col(f);
      for (let i = 0; i < df.n; i++) {
        const num = parseNum(vals[i]);
        if (num !== null && (num < lo || num > hi)) sink.add(rule, table, f, pkcol[i], pid[i], `${f}=${vals[i]} 범위 [${loTxt},${hiTxt}] 밖`);
      }
    } else if (chk === "pattern") {
      const f = fields[0];
      // Python re.match 는 문자열 시작에만 고정된다
      const rx = new RegExp(`^(?:${p.regex as string})`);
      const vals = col(f);
      for (let i = 0; i < df.n; i++) {
        const v = vals[i];
        if (v !== "" && !rx.test(v)) sink.add(rule, table, f, pkcol[i], pid[i], `${f}='${v}' 패턴 불일치`);
      }
    } else if (chk === "not_future") {
      const f = fields[0]; const vals = col(f);
      for (let i = 0; i < df.n; i++) {
        const v = vals[i];
        if (v === "") continue;
        const ms = parseIsoDate(v);
        if (ms !== null && ms > todayMs) sink.add(rule, table, f, pkcol[i], pid[i], `${f}=${v} 미래 날짜`);
      }
    } else if (chk === "group_anchor") {
      const anchor = p.anchor as string;
      const members = (p.members as string[]).filter((m) => df.cols.has(m));
      if (!df.cols.has(anchor) || members.length === 0) { st.status = "skipped"; st.note = "anchor/멤버 컬럼 없음"; continue; }
      const acol = col(anchor);
      const mcols = members.map((m) => col(m));
      for (let i = 0; i < df.n; i++) {
        if (acol[i] !== "") continue;
        const filled: string[] = [];
        for (let j = 0; j < members.length; j++) if (mcols[j][i] !== "") { filled.push(members[j]); if (filled.length === 3) break; }
        if (filled.length) sink.add(rule, table, anchor, pkcol[i], pid[i], `${pyList(filled)} 값 있으나 anchor ${anchor} NULL`);
      }
    } else if (chk === "person_invariant") {
      const fs = (p.fields as string[]).filter((f) => df.cols.has(f));
      if (!df.cols.has("person_id") || fs.length === 0) { st.status = "skipped"; continue; }
      const pcol = col("person_id");
      for (const f of fs) {
        const vals = col(f);
        const byPerson = new Map<string, Set<string>>();
        for (let i = 0; i < df.n; i++) {
          if (vals[i] === "") continue;
          let s = byPerson.get(pcol[i]);
          if (!s) { s = new Set(); byPerson.set(pcol[i], s); }
          s.add(vals[i]);
        }
        for (const person of pySorted(byPerson.keys())) {
          const s = byPerson.get(person)!;
          if (s.size > 1) sink.add(rule, table, f, "", person, `${f} 값이 환자 내에서 다름: ${pyList(pySorted(s))}`);
        }
      }
    } else if (chk === "must_be_null") {
      const f = fields[0]; const vals = col(f);
      for (let i = 0; i < df.n; i++) if (vals[i] !== "") sink.add(rule, table, f, pkcol[i], pid[i], `${f}=${vals[i]} (이 코호트에서는 NULL 이어야 함)`);
    } else {
      st.status = "error"; st.note = `알 수 없는 검사 유형: ${chk}`;
    }
  }
}
