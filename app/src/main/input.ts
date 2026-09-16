// 입력 처리: 파일 인식(CSV · 엑셀 시트) → 테이블 자동 대응 → 사전 점검 → 정규화(UTF-8 CSV 스테이징) → 양식 생성
import fs from "node:fs";
import path from "node:path";
import * as XLSX from "xlsx";
import { parse } from "csv-parse/sync";
import { csvCell } from "@engine/csv.js";
import type { Spec, SpecTable } from "@engine/types.js";
import type { SourceCandidate, TableCheck, InputPlan, PreviewData, InputIssue } from "@shared/types";

const SAMPLE_ROWS = 20;
const ALIASES: Record<string, string> = { antp_therapy_id: "antp_id" };
/** 병원 내보내기가 빈 값 대신 적어 두는 글자들. 이것은 데이터가 아니라 도구의 흔적이라 빈 값으로 본다. */
const NULL_STRINGS = new Set(["NULL", "null", "Null", "NA", "N/A", "n/a", "#N/A", "None", "nan", "NaN"]);

/**
 * 첫 줄을 보고 구분자를 정한다. 쉼표가 기본이지만 유럽식 엑셀은 세미콜론을, 일부 도구는 탭을 쓴다.
 * 따옴표 밖의 글자만 센다.
 */
export function sniffDelimiter(text: string, ext: string): string {
  if (ext === ".tsv") return "\t";
  const nl = text.indexOf("\n");
  const head = nl < 0 ? text : text.slice(0, nl);
  const count: Record<string, number> = { ",": 0, ";": 0, "\t": 0, "|": 0 };
  let q = false;
  for (const ch of head) {
    if (ch === '"') q = !q;
    else if (!q && ch in count) count[ch]++;
  }
  const best = Object.entries(count).sort((a, b) => b[1] - a[1])[0];
  return best[1] > 0 ? best[0] : ",";
}

/**
 * 파일의 컬럼명을 명세 컬럼명으로 잇는다. 그대로 같으면 그대로, 대소문자만 다르면 소문자로,
 * 알려진 별칭이면 그것으로. 잇지 못한 것은 그대로 둔다(명세에 없는 컬럼).
 */
export function columnAliases(columns: string[], specCols: string[]): { map: Record<string, string>; caseFolded: string[]; aliased: string[] } {
  const exact = new Set(specCols);
  const lower = new Map(specCols.map((c) => [c.toLowerCase(), c]));
  const map: Record<string, string> = {};
  const caseFolded: string[] = [];
  const aliased: string[] = [];
  for (const c of columns) {
    if (exact.has(c)) { map[c] = c; continue; }
    const byCase = lower.get(c.toLowerCase());
    if (byCase && !columns.includes(byCase)) { map[c] = byCase; caseFolded.push(c); continue; }
    const byAlias = ALIASES[c] ?? ALIASES[c.toLowerCase()];
    if (byAlias && !columns.includes(byAlias)) { map[c] = byAlias; aliased.push(`${c} → ${byAlias}`); continue; }
    map[c] = c;
  }
  return { map, caseFolded, aliased };
}
const DATE_RE = /^\d{4}-\d{2}-\d{2}$/;
const TS_RE = /^\d{4}-\d{2}-\d{2}([ T]\d{2}:\d{2}(:\d{2}(\.\d+)?)?)?$/;

// ------------------------------------------------------------------ 인코딩
export interface Encoding { name: "utf-8" | "euc-kr"; bom: boolean; label: string }

/** UTF-8 이면 그대로, 아니면 EUC-KR(CP949) 로 시도한다. 둘 다 아니면 예외. */
export function detectEncoding(buf: Buffer): Encoding {
  const bom = buf.length >= 3 && buf[0] === 0xef && buf[1] === 0xbb && buf[2] === 0xbf;
  const head = buf.subarray(0, Math.min(buf.length, 512 * 1024));
  try {
    new TextDecoder("utf-8", { fatal: true }).decode(head, { stream: true });
    return { name: "utf-8", bom, label: bom ? "UTF-8 (BOM)" : "UTF-8" };
  } catch { /* 다음 후보 */ }
  try {
    new TextDecoder("euc-kr", { fatal: true }).decode(head, { stream: true });
    return { name: "euc-kr", bom: false, label: "EUC-KR (CP949) → UTF-8 로 변환" };
  } catch {
    throw new Error("문자 인코딩을 알 수 없습니다 (UTF-8 또는 EUC-KR 이어야 합니다)");
  }
}

export function readText(p: string): { text: string; encoding: Encoding } {
  const buf = fs.readFileSync(p);
  const encoding = detectEncoding(buf);
  const text = new TextDecoder(encoding.name).decode(encoding.bom ? buf.subarray(3) : buf);
  return { text, encoding };
}

/** 따옴표 밖의 줄바꿈만 세어 데이터 행 수를 구한다 (헤더 제외) */
function countCsvRows(text: string): number {
  let n = 0, q = false, lastNl = -1;
  for (let i = 0; i < text.length; i++) {
    const ch = text.charCodeAt(i);
    if (ch === 34) q = !q; // "
    else if (ch === 10 && !q) { n++; lastNl = i; }
  }
  if (lastNl < text.length - 1 && text.slice(lastNl + 1).trim() !== "") n++;
  return Math.max(0, n - 1);
}

// ------------------------------------------------------------------ 파일 인식
const EXT_CSV = new Set([".csv", ".txt", ".tsv"]);
const EXT_XLSX = new Set([".xlsx", ".xlsm", ".xls"]);

function filesIn(dir: string): string[] {
  const out: string[] = [];
  for (const f of fs.readdirSync(dir).sort()) {
    const ext = path.extname(f).toLowerCase();
    if (!f.startsWith(".") && !f.startsWith("_") && (EXT_CSV.has(ext) || EXT_XLSX.has(ext))) out.push(path.join(dir, f));
  }
  return out;
}

/**
 * 폴더는 그 안의 CSV/엑셀 파일로 펼친다.
 * 폴더에 직접 든 파일이 하나도 없으면 바로 아래 폴더까지만 들여다본다 —
 * v2 는 서식을 바꾼 폴더와 EHR 추출본 폴더가 따로 오므로, 그 둘을 담은 상위 폴더를
 * 통째로 끌어다 놓는 일이 흔하다. 그보다 깊이는 보지 않는다.
 */
export function expandPaths(paths: string[]): string[] {
  const out: string[] = [];
  for (const p of paths) {
    if (!fs.existsSync(p)) continue;
    if (fs.statSync(p).isDirectory()) {
      const here = filesIn(p);
      if (here.length) { out.push(...here); continue; }
      for (const d of fs.readdirSync(p).sort()) {
        const sub = path.join(p, d);
        if (!d.startsWith(".") && !d.startsWith("_") && fs.existsSync(sub) && fs.statSync(sub).isDirectory()) out.push(...filesIn(sub));
      }
    } else out.push(p);
  }
  return [...new Set(out)];
}

export function cellToString(v: unknown): string {
  if (v === null || v === undefined) return "";
  if (v instanceof Date) {
    if (Number.isNaN(v.getTime())) return "";
    const p = (x: number) => String(x).padStart(2, "0");
    const d = `${v.getFullYear()}-${p(v.getMonth() + 1)}-${p(v.getDate())}`;
    const hasTime = v.getHours() || v.getMinutes() || v.getSeconds();
    return hasTime ? `${d} ${p(v.getHours())}:${p(v.getMinutes())}:${p(v.getSeconds())}` : d;
  }
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : String(v);
  if (typeof v === "boolean") return v ? "1" : "0";
  return String(v);
}

function inspectCsv(p: string): SourceCandidate {
  const base = { id: p, kind: "csv" as const, path: p, name: path.basename(p), folder: path.dirname(p), sizeBytes: fs.statSync(p).size };
  try {
    const { text, encoding } = readText(p);
    if (!text.trim()) return { ...base, rows: 0, columns: [], sample: [], encoding: encoding.label, error: "빈 파일입니다" };
    const delimiter = sniffDelimiter(text, path.extname(p).toLowerCase());
    const head: string[][] = parse(text, { to_line: SAMPLE_ROWS + 1, relax_column_count: true, skip_empty_lines: true, delimiter });
    const { columns, keep } = headerOf(head[0] ?? []);
    const sample = head.slice(1).map((r) => keep.map((k) => (r[k] ?? "").trim()));
    return { ...base, rows: countCsvRows(text), columns, sample, encoding: encoding.label, delimiter: delimiter === "," ? undefined : delimiter };
  } catch (e) {
    return { ...base, rows: 0, columns: [], sample: [], encoding: "?", error: (e as Error).message };
  }
}

/**
 * 헤더를 정리한다: 양끝 공백을 걷고, 이름이 빈 끝 컬럼(엑셀이 남기는 ',,,')은 버린다.
 * keep 은 남긴 컬럼의 원래 자리다 — 값 행도 같은 자리만 가져온다.
 */
function headerOf(raw: string[]): { columns: string[]; keep: number[]; dropped: number } {
  const trimmed = raw.map((c) => String(c).trim());
  let end = trimmed.length;
  while (end > 0 && trimmed[end - 1] === "") end--;
  const keep = Array.from({ length: end }, (_, i) => i);
  return { columns: trimmed.slice(0, end), keep, dropped: trimmed.length - end };
}

/** 엑셀의 시트를 문자열 행렬로 (날짜 셀은 ISO 로) */
function sheetRows(ws: XLSX.WorkSheet): string[][] {
  const raw = XLSX.utils.sheet_to_json<unknown[]>(ws, { header: 1, raw: true, defval: "", blankrows: false });
  return raw.map((r) => r.map(cellToString));
}

function inspectXlsx(p: string): SourceCandidate[] {
  const size = fs.statSync(p).size;
  try {
    const wb = XLSX.readFile(p, { cellDates: true });
    return wb.SheetNames.map((sheet) => {
      const rows = sheetRows(wb.Sheets[sheet]);
      const { columns, keep } = headerOf(rows[0] ?? []);
      const sample = rows.slice(1, SAMPLE_ROWS + 1).map((r) => keep.map((k) => (r[k] ?? "").trim()));
      return { id: `${p}#${sheet}`, kind: "xlsx" as const, path: p, sheet, name: `${path.basename(p)} / ${sheet}`, folder: path.dirname(p),
        rows: Math.max(0, rows.length - 1), columns, sample, encoding: "엑셀", sizeBytes: size };
    });
  } catch (e) {
    return [{ id: p, kind: "xlsx", path: p, name: path.basename(p), folder: path.dirname(p), rows: 0, columns: [], sample: [], encoding: "엑셀", sizeBytes: size, error: (e as Error).message }];
  }
}

export function inspectPaths(paths: string[]): SourceCandidate[] {
  const out: SourceCandidate[] = [];
  for (const p of expandPaths(paths)) {
    const ext = path.extname(p).toLowerCase();
    if (EXT_XLSX.has(ext)) out.push(...inspectXlsx(p));
    else out.push(inspectCsv(p));
  }
  return out;
}

// ------------------------------------------------------------------ 값 정규화
// 내보내기 도구의 흔적을 걷어 낸다. 데이터를 고치는 것이 아니라 표기를 되돌리는 것이라
// 뜻이 하나로 정해지는 경우만 손댄다: 정수 자리의 '123.0', 날짜 자리의 '2022-01-01 00:00:00',
// 어디서나 'NULL' 글자와 양끝 공백. '1,234' 나 '2022/01/01' 은 손대지 않는다 — 규칙이 보고한다.
const INT_FLOAT_RE = /^-?\d+\.0+$/;
const ZERO_TIME_RE = /^(\d{4}-\d{2}-\d{2})[ T]00:00(:00(\.0+)?)?$/;

export interface NormReport { trimmed: number; nullStrings: number; intFloats: number; zeroTimes: number; droppedColumns: number; caseFolded: number; aliased: number }
const emptyReport = (): NormReport => ({ trimmed: 0, nullStrings: 0, intFloats: 0, zeroTimes: 0, droppedColumns: 0, caseFolded: 0, aliased: 0 });

/** 한 칸을 정리한다. 무엇을 했는지는 report 에 센다. */
function normalizeCell(raw: string, type: string, report?: NormReport): string {
  let v = raw;
  const t = v.trim();
  if (t !== v) { v = t; if (report) report.trimmed++; }
  if (v === "") return v;
  if (NULL_STRINGS.has(v)) { if (report) report.nullStrings++; return ""; }
  if ((type === "integer" || type === "bigint") && INT_FLOAT_RE.test(v)) { if (report) report.intFloats++; return v.slice(0, v.indexOf(".")); }
  if (type === "date") { const m = ZERO_TIME_RE.exec(v); if (m) { if (report) report.zeroTimes++; return m[1]; } }
  return v;
}

/** 표본 20행에서 흔적을 센다 (사전 점검 안내용) */
function sampleMarks(c: SourceCandidate, st: SpecTable, aliasMap: Record<string, string>): NormReport {
  const r = emptyReport();
  const typeOf = new Map(st.fields.map((f) => [f.name, f.type as string]));
  c.columns.forEach((col, j) => {
    const type = typeOf.get(aliasMap[col]) ?? "varchar";
    for (const row of c.sample) normalizeCell(row[j] ?? "", type, r);
  });
  r.trimmed = 0;   // 표본은 이미 걷어 낸 값이라 세지 않는다
  return r;
}

// ------------------------------------------------------------------ 자동 대응
const norm = (s: string) => s.toUpperCase().replace(/[^A-Z0-9]/g, "");

/** 후보의 이름(시트명 또는 확장자 뺀 파일명)을 테이블 이름과 견줄 수 있게 정규화 */
function nameOfCandidate(c: SourceCandidate): string {
  return norm(c.sheet ?? path.basename(c.path, path.extname(c.path)));
}

/** 폴더를 화면에 짧게 적는다 (상위 한 칸까지) */
export function folderLabel(dir: string): string {
  const parent = path.basename(path.dirname(dir));
  const here = path.basename(dir);
  return parent && parent !== here && parent !== path.sep ? `${parent}/${here}` : here;
}

function headerSimilarity(columns: string[], t: SpecTable): number {
  if (!columns.length) return 0;
  const spec = t.fields.map((f) => f.name);
  const have = new Set(Object.values(columnAliases(columns, spec).map));
  const hit = spec.filter((c) => have.has(c)).length;
  return hit / Math.max(spec.length, 1);
}

/**
 * 파일 이름 → 테이블 이름 → 헤더 유사도 순으로 대응시킨다.
 * 이름이 테이블과 같은 파일이 여러 폴더에서 오면 모두 그 테이블로 잇는다(합쳐 읽는다).
 * v2 는 EHR 추출본과 서식 변환 결과가 같은 OMOP 표(MEASUREMENT 등)를 나눠 갖기 때문이다.
 */
export function autoMatch(tables: string[], spec: Spec, candidates: SourceCandidate[]): Record<string, string[]> {
  const mapping: Record<string, string[]> = {};
  const used = new Set<string>();
  const cands = candidates.filter((c) => !c.error);
  const byLen = [...tables].sort((a, b) => b.length - a.length); // 긴 이름 먼저 (VISIT_OCCURRENCE 가 VISIT 보다 먼저)
  // 1) 파일명(또는 시트명)이 테이블명과 같음 — 전부.
  //    읽지 못한 파일도 이름이 맞으면 잇는다. 그래야 "파일 없음"이 아니라 "읽을 수 없음"으로 그 표 줄에 나온다.
  for (const t of byLen) {
    const hits = candidates.filter((c) => !used.has(c.id) && nameOfCandidate(c) === norm(t));
    const ok = hits.filter((c) => !c.error);
    const pick = ok.length ? ok : hits.slice(0, 1);
    if (pick.length) { mapping[t] = pick.map((c) => c.id); pick.forEach((c) => used.add(c.id)); }
  }
  // 2) 파일명이 테이블명을 포함 (하나만)
  for (const t of byLen) {
    if (mapping[t]) continue;
    const hit = cands.find((c) => !used.has(c.id) && nameOfCandidate(c).includes(norm(t)));
    if (hit) { mapping[t] = [hit.id]; used.add(hit.id); }
  }
  // 3) 헤더 유사도 (명세 컬럼의 60% 이상이면, 하나만)
  for (const t of tables) {
    if (mapping[t]) continue;
    let best: SourceCandidate | null = null, bestScore = 0;
    for (const c of cands) {
      if (used.has(c.id)) continue;
      const s = headerSimilarity(c.columns, spec.tables[t]);
      if (s > bestScore) { best = c; bestScore = s; }
    }
    if (best && bestScore >= 0.6) { mapping[t] = [best.id]; used.add(best.id); }
  }
  return mapping;
}

// ------------------------------------------------------------------ 사전 점검
export function checkTables(tables: string[], spec: Spec, candidates: SourceCandidate[], mapping: Record<string, string[]>, auto: Record<string, string[]>, requiredTables: string[] = ["PERSON"]): TableCheck[] {
  const byId = new Map(candidates.map((c) => [c.id, c]));
  const req = new Set(requiredTables);
  const same = (a: string[] = [], b: string[] = []) => a.length === b.length && a.every((x, i) => x === b[i]);
  return tables.map((table) => {
    const st = spec.tables[table];
    const required = req.has(table);
    const ids = (mapping[table] ?? []).filter((id) => byId.has(id));
    const cs = ids.map((id) => byId.get(id)!);
    const issues: InputIssue[] = [];
    const out: TableCheck = { table, kor: st.kor, required, candidateIds: ids, auto: ids.length > 0 && same(auto[table], ids), rows: null, missingColumns: [], extraColumns: [], aliases: [], issues };
    if (!cs.length) {
      issues.push(required
        ? { level: "error", text: "파일이 없습니다. 이 테이블 없이는 검증할 수 없습니다." }
        : { level: "warn", text: "파일이 없습니다. 이 테이블의 규칙은 건너뛰고 '테이블 없음'으로 보고됩니다. 해당 사례가 없더라도 헤더만 있는 빈 파일을 넣어 주세요." });
      return out;
    }
    const broken = cs.filter((c) => c.error);
    if (broken.length) { for (const c of broken) issues.push({ level: "error", text: `파일을 읽을 수 없습니다 (${c.name}): ${c.error}` }); return out; }
    out.rows = cs.reduce((n, c) => n + c.rows, 0);
    const specCols = st.fields.map((f) => f.name);
    // 합칠 때는 컬럼을 이름으로 맞춘다. 파일마다 컬럼이 다르면 없는 자리는 빈 값이 된다 — 그것을 말해 준다.
    if (cs.length > 1) {
      issues.push({ level: "info", text: `${cs.length}개 파일을 합쳐 읽습니다: ${cs.map((c) => `${folderLabel(c.folder)} ${c.rows.toLocaleString("ko-KR")}행`).join(" + ")}.` });
      const sets = cs.map((c) => new Set(Object.values(columnAliases(c.columns, specCols).map)));
      const all = new Set(sets.flatMap((x) => [...x]));
      const uneven = cs.filter((_, i) => sets[i].size !== all.size);
      if (uneven.length) issues.push({ level: "warn", text: `합치는 파일들의 컬럼 구성이 다릅니다 (${uneven.map((c) => folderLabel(c.folder)).join(", ")}). 없는 컬럼은 빈 값으로 채웁니다.` });
    }
    const have = new Set<string>();
    for (const c of cs) {
      const al = columnAliases(c.columns, specCols);
      for (const v of Object.values(al.map)) have.add(v);
      for (const a of al.aliased) if (!out.aliases.includes(a)) out.aliases.push(a);
      if (al.caseFolded.length) issues.push({ level: "info", text: `컬럼명 대소문자가 다릅니다 (${al.caseFolded.length}개, 예: ${al.caseFolded[0]}). 소문자로 맞춰 읽습니다.` });
      if (c.delimiter) issues.push({ level: "info", text: `구분자가 '${c.delimiter === "\t" ? "탭" : c.delimiter}' 입니다. 그대로 읽습니다.` });
      // 표본에서 내보내기 흔적을 미리 센다. 실제 정규화는 실행할 때 전체 행에 한다.
      const marks = sampleMarks(c, st, al.map);
      if (marks.nullStrings) issues.push({ level: "info", text: `'NULL'·'NA' 같은 글자가 표본에 ${marks.nullStrings}개 있습니다. 빈 값으로 읽습니다.` });
      if (marks.intFloats) issues.push({ level: "info", text: `정수 컬럼에 '.0' 이 붙은 값이 표본에 ${marks.intFloats}개 있습니다 (예: 100001.0). 정수로 읽습니다.` });
      if (marks.zeroTimes) issues.push({ level: "info", text: `날짜 컬럼에 '00:00:00' 이 붙은 값이 표본에 ${marks.zeroTimes}개 있습니다. 날짜만 읽습니다.` });
      if (c.columns.some((n, i) => c.columns.indexOf(n) !== i)) issues.push({ level: "error", text: `중복된 컬럼명이 있습니다 (${c.name}).` });
      if (c.rows === 0) issues.push({ level: "warn", text: `데이터 행이 없습니다 (헤더만): ${c.name}` });
      // 날짜 형식 표본
      for (const f of st.fields) {
        if (f.type !== "date" && f.type !== "timestamp") continue;
        const idx = c.columns.findIndex((n) => al.map[n] === f.name);
        if (idx < 0) continue;
        // 00:00:00 이 붙은 날짜는 정규화가 걷어 내므로 여기서 나무라지 않는다
        const bad = c.sample.map((r) => normalizeCell(r[idx] ?? "", f.type)).filter((v) => v !== "" && !(f.type === "date" ? DATE_RE : TS_RE).test(v));
        if (bad.length) issues.push({ level: "warn", text: `${f.name} 날짜 형식이 다릅니다 (예: '${bad[0]}'). YYYY-MM-DD 여야 하며, 이대로면 타입 규칙에 걸립니다.` });
      }
    }
    out.missingColumns = specCols.filter((n) => !have.has(n));
    out.extraColumns = [...new Set(cs.flatMap((c) => { const m = columnAliases(c.columns, specCols).map; return c.columns.filter((n) => !specCols.includes(m[n])); }))];
    if (out.missingColumns.includes(st.pk)) issues.push({ level: "error", text: `기본키 컬럼 ${st.pk} 이(가) 없습니다.` });
    if (table !== "PERSON" && specCols.includes("person_id") && out.missingColumns.includes("person_id")) issues.push({ level: "error", text: "person_id 컬럼이 없습니다." });
    const otherMissing = out.missingColumns.filter((n) => n !== st.pk && n !== "person_id");
    if (otherMissing.length) issues.push({ level: "warn", text: `명세 컬럼 ${otherMissing.length}개 없음: ${otherMissing.slice(0, 6).join(", ")}${otherMissing.length > 6 ? " …" : ""}` });
    if (out.extraColumns.length) issues.push({ level: "info", text: `명세에 없는 컬럼 ${out.extraColumns.length}개 (무시됨): ${out.extraColumns.slice(0, 6).join(", ")}${out.extraColumns.length > 6 ? " …" : ""}` });
    for (const a of out.aliases) issues.push({ level: "info", text: `별칭 컬럼 해석: ${a}` });
    return out;
  });
}

export function buildPlan(cohort: string, tables: string[], spec: Spec, candidates: SourceCandidate[], mapping?: Record<string, string[]>, requiredTables?: string[]): InputPlan {
  const auto = autoMatch(tables, spec, candidates);
  const m = mapping ?? auto;
  const checks = checkTables(tables, spec, candidates, m, auto, requiredTables);
  const errors = checks.reduce((n, t) => n + t.issues.filter((i) => i.level === "error").length, 0);
  const warnings = checks.reduce((n, t) => n + t.issues.filter((i) => i.level === "warn").length, 0);
  return { cohort, candidates, mapping: m, tables: checks, errors, warnings, ok: errors === 0 };
}

// ------------------------------------------------------------------ 미리보기
export function preview(c: SourceCandidate, limit = 50): PreviewData {
  if (c.kind === "xlsx" && c.sheet !== undefined) {
    const wb = XLSX.readFile(c.path, { cellDates: true, sheetRows: limit + 1 });
    const rows = sheetRows(wb.Sheets[c.sheet]);
    return { columns: rows[0] ?? [], rows: rows.slice(1, limit + 1), total: c.rows };
  }
  const { text } = readText(c.path);
  const rows: string[][] = parse(text, { to_line: limit + 1, relax_column_count: true, skip_empty_lines: true, delimiter: sniffDelimiter(text, path.extname(c.path).toLowerCase()) });
  return { columns: rows[0] ?? [], rows: rows.slice(1), total: c.rows };
}

// ------------------------------------------------------------------ 스테이징 (정규화된 입력 폴더)
/**
 * 대응된 파일을 <TABLE>.csv (UTF-8, 쉼표) 로 옮긴다. 엑셀 시트는 CSV 로, EUC-KR 은 UTF-8 로,
 * 세미콜론·탭 구분은 쉼표로. 컬럼명은 명세 이름으로 잇고(대소문자·별칭), 값은 normalizeCell 로 정리한다.
 * 무엇을 얼마나 손댔는지 표별로 돌려준다 — 보고서에 적어 병원이 알 수 있게.
 */
export function stageInputs(candidates: SourceCandidate[], mapping: Record<string, string[]>, dir: string, spec: Spec): Record<string, NormReport> {
  fs.mkdirSync(dir, { recursive: true });
  const byId = new Map(candidates.map((c) => [c.id, c]));
  const opened = new Map<string, XLSX.WorkBook>();
  const reports: Record<string, NormReport> = {};
  const readRows = (c: SourceCandidate): string[][] => {
    if (c.kind === "xlsx" && c.sheet !== undefined) {
      let wb = opened.get(c.path);
      if (!wb) { wb = XLSX.readFile(c.path, { cellDates: true }); opened.set(c.path, wb); }
      return sheetRows(wb.Sheets[c.sheet]);
    }
    const { text } = readText(c.path);
    return parse(text, { relax_column_count: true, skip_empty_lines: true, delimiter: sniffDelimiter(text, path.extname(c.path).toLowerCase()) });
  };
  for (const [table, ids] of Object.entries(mapping)) {
    const cs = ids.map((id) => byId.get(id)).filter((c): c is SourceCandidate => !!c && !c.error);
    const st = spec.tables[table]; if (!st || !cs.length) continue;
    const report = emptyReport();
    const specCols = st.fields.map((f) => f.name);
    const typeOf = new Map(st.fields.map((f) => [f.name, f.type as string]));
    // 파일마다 (명세 이름으로 이은 컬럼, 남긴 자리, 값 행) 을 읽어 둔다. 합칠 컬럼은 처음 본 차례대로 모은다.
    const parts: Array<{ cols: string[]; keep: number[]; rows: string[][] }> = [];
    const columns: string[] = [];
    for (const c of cs) {
      const rows = readRows(c);
      const { columns: rawCols, keep, dropped } = headerOf(rows[0] ?? []);
      report.droppedColumns += dropped;
      const al = columnAliases(rawCols, specCols);
      report.caseFolded += al.caseFolded.length;
      report.aliased += al.aliased.length;
      const cols = rawCols.map((n) => al.map[n]);
      for (const n of cols) if (!columns.includes(n)) columns.push(n);
      parts.push({ cols, keep, rows: rows.slice(1) });
    }
    const types = columns.map((n) => typeOf.get(n) ?? "varchar");
    const lines = [columns.map(csvCell).join(",")];
    for (const part of parts) {
      // 이 파일의 자리 → 합친 컬럼의 자리
      const at = columns.map((n) => { const j = part.cols.indexOf(n); return j < 0 ? -1 : part.keep[j]; });
      for (const r of part.rows) {
        lines.push(at.map((k, j) => csvCell(k < 0 ? "" : normalizeCell(r[k] ?? "", types[j], report))).join(","));
      }
    }
    fs.writeFileSync(path.join(dir, `${table}.csv`), lines.join("\n") + "\n", "utf-8");
    reports[table] = report;
  }
  return reports;
}

// ------------------------------------------------------------------ 입력 양식
function specRows(tables: string[], spec: Spec): (string | number | boolean)[][] {
  const rows: (string | number | boolean)[][] = [["테이블", "테이블(한글)", "순서", "컬럼", "컬럼(한글)", "타입", "필수", "키", "참조", "코드표", "범위", "패턴", "설명"]];
  for (const t of tables) {
    const st = spec.tables[t];
    st.fields.forEach((f, i) => {
      const range = Array.isArray(f.range) ? `${(f.range as number[])[0]} ~ ${(f.range as number[])[1]}` : "";
      // 코드표 이름은 v1 이 codelist, v2 가 concept_set 이다
      const codes = f.codelist ?? f.concept_set;
      rows.push([t, st.kor, i + 1, f.name, String(f.kor ?? ""), f.type, f.required ? "Y" : "", String(f.key ?? ""), String(f.ref ?? ""), String(codes ?? ""), range, String(f.pattern ?? ""), String(f.desc ?? "")]);
    });
  }
  return rows;
}

/** 헤더만 있는 CSV 묶음을 폴더에 쓴다 */
export function writeCsvTemplates(tables: string[], spec: Spec, dir: string): string[] {
  fs.mkdirSync(dir, { recursive: true });
  const out: string[] = [];
  for (const t of tables) {
    const p = path.join(dir, `${t}.csv`);
    fs.writeFileSync(p, "\uFEFF" + spec.tables[t].fields.map((f) => f.name).join(",") + "\n", "utf-8");
    out.push(p);
  }
  fs.writeFileSync(path.join(dir, "README.txt"), [
    "K-AI 코호트 데이터 입력 양식 (CSV)", "",
    "- 파일 하나가 테이블 하나입니다. 파일 이름은 바꾸지 마세요.",
    "- 첫 줄은 컬럼명입니다. 순서는 바꿔도 되지만 이름은 바꾸지 마세요.",
    "- 인코딩 UTF-8, 빈 값은 빈 칸, 날짜는 YYYY-MM-DD, 타임스탬프는 YYYY-MM-DD HH:MM:SS 입니다.",
    "- 컬럼 설명은 컬럼 명세서(xlsx)를 참고하세요.", ""].join("\n"), "utf-8");
  return out;
}

/** 시트당 테이블 하나인 엑셀 양식 (+ 명세 시트) */
export function writeXlsxTemplate(tables: string[], spec: Spec, file: string): void {
  const wb = XLSX.utils.book_new();
  const guide = [["K-AI 코호트 데이터 입력 양식 (엑셀)"], [""], ["시트 하나가 테이블 하나입니다. 시트 이름은 바꾸지 마세요."], ["첫 줄은 컬럼명입니다. 이름은 바꾸지 마세요."], ["빈 값은 빈 칸으로 두고, 날짜는 날짜 셀 또는 YYYY-MM-DD 문자열로 넣습니다."], ["컬럼 설명은 '명세' 시트를 보세요."]];
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(guide), "안내");
  for (const t of tables) {
    const ws = XLSX.utils.aoa_to_sheet([spec.tables[t].fields.map((f) => f.name)]);
    XLSX.utils.book_append_sheet(wb, ws, t.slice(0, 31));
  }
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(specRows(tables, spec)), "명세");
  XLSX.writeFile(wb, file);
}

/** 컬럼 명세서 (xlsx) */
export function writeSpecSheet(tables: string[], spec: Spec, file: string): void {
  const wb = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(specRows(tables, spec)), "컬럼 명세");
  XLSX.writeFile(wb, file);
}
