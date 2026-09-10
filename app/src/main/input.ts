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

/** 폴더는 그 안의 CSV/엑셀 파일로 펼친다 (하위 폴더는 보지 않음) */
export function expandPaths(paths: string[]): string[] {
  const out: string[] = [];
  for (const p of paths) {
    if (!fs.existsSync(p)) continue;
    if (fs.statSync(p).isDirectory()) {
      for (const f of fs.readdirSync(p).sort()) {
        const ext = path.extname(f).toLowerCase();
        if (!f.startsWith(".") && !f.startsWith("_") && (EXT_CSV.has(ext) || EXT_XLSX.has(ext))) out.push(path.join(p, f));
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
  const base = { id: p, kind: "csv" as const, path: p, name: path.basename(p), sizeBytes: fs.statSync(p).size };
  try {
    const { text, encoding } = readText(p);
    const delimiter = path.extname(p).toLowerCase() === ".tsv" ? "\t" : ",";
    const head: string[][] = parse(text, { to_line: SAMPLE_ROWS + 1, relax_column_count: true, skip_empty_lines: true, delimiter });
    const columns = (head[0] ?? []).map((c) => c.trim());
    return { ...base, rows: countCsvRows(text), columns, sample: head.slice(1), encoding: encoding.label };
  } catch (e) {
    return { ...base, rows: 0, columns: [], sample: [], encoding: "?", error: (e as Error).message };
  }
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
      const columns = (rows[0] ?? []).map((c) => String(c).trim());
      return { id: `${p}#${sheet}`, kind: "xlsx" as const, path: p, sheet, name: `${path.basename(p)} / ${sheet}`,
        rows: Math.max(0, rows.length - 1), columns, sample: rows.slice(1, SAMPLE_ROWS + 1), encoding: "엑셀", sizeBytes: size };
    });
  } catch (e) {
    return [{ id: p, kind: "xlsx", path: p, name: path.basename(p), rows: 0, columns: [], sample: [], encoding: "엑셀", sizeBytes: size, error: (e as Error).message }];
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

// ------------------------------------------------------------------ 자동 대응
const norm = (s: string) => s.toUpperCase().replace(/[^A-Z0-9]/g, "");

function headerSimilarity(columns: string[], t: SpecTable): number {
  if (!columns.length) return 0;
  const have = new Set(columns.map((c) => ALIASES[c] ?? c));
  const spec = t.fields.map((f) => f.name);
  const hit = spec.filter((c) => have.has(c)).length;
  return hit / Math.max(spec.length, 1);
}

/** 파일 이름 → 테이블 이름 → 헤더 유사도 순으로 대응시킨다 */
export function autoMatch(tables: string[], spec: Spec, candidates: SourceCandidate[]): Record<string, string> {
  const mapping: Record<string, string> = {};
  const used = new Set<string>();
  const cands = candidates.filter((c) => !c.error);
  const byLen = [...tables].sort((a, b) => b.length - a.length); // 긴 이름 먼저 (VISIT_OCCURRENCE 가 VISIT 보다 먼저)
  // 1) 파일명(또는 시트명)이 테이블명과 같음
  for (const t of byLen) {
    const hit = cands.find((c) => !used.has(c.id) && (norm(c.sheet ?? path.basename(c.path, path.extname(c.path))) === norm(t)));
    if (hit) { mapping[t] = hit.id; used.add(hit.id); }
  }
  // 2) 파일명이 테이블명을 포함
  for (const t of byLen) {
    if (mapping[t]) continue;
    const hit = cands.find((c) => !used.has(c.id) && norm(c.sheet ?? path.basename(c.path, path.extname(c.path))).includes(norm(t)));
    if (hit) { mapping[t] = hit.id; used.add(hit.id); }
  }
  // 3) 헤더 유사도 (명세 컬럼의 60% 이상이 있으면)
  for (const t of tables) {
    if (mapping[t]) continue;
    let best: SourceCandidate | null = null, bestScore = 0;
    for (const c of cands) {
      if (used.has(c.id)) continue;
      const s = headerSimilarity(c.columns, spec.tables[t]);
      if (s > bestScore) { best = c; bestScore = s; }
    }
    if (best && bestScore >= 0.6) { mapping[t] = best.id; used.add(best.id); }
  }
  return mapping;
}

// ------------------------------------------------------------------ 사전 점검
export function checkTables(tables: string[], spec: Spec, candidates: SourceCandidate[], mapping: Record<string, string>, auto: Record<string, string>): TableCheck[] {
  const byId = new Map(candidates.map((c) => [c.id, c]));
  const disease = tables.find((t) => spec.tables[t].category === "disease");
  return tables.map((table) => {
    const st = spec.tables[table];
    const required = table === "PERSON" || table === disease;
    const cid = mapping[table] ?? null;
    const c = cid ? byId.get(cid) ?? null : null;
    const issues: InputIssue[] = [];
    const out: TableCheck = { table, kor: st.kor, required, candidateId: cid, auto: !!cid && auto[table] === cid, rows: null, missingColumns: [], extraColumns: [], aliases: [], issues };
    if (!c) {
      issues.push(required ? { level: "error", text: "파일이 없습니다. 이 테이블 없이는 검증할 수 없습니다." } : { level: "warn", text: "파일이 없습니다. 이 테이블의 규칙은 건너뜁니다." });
      return out;
    }
    if (c.error) { issues.push({ level: "error", text: `파일을 읽을 수 없습니다: ${c.error}` }); return out; }
    out.rows = c.rows;
    const have = new Set<string>();
    for (const col of c.columns) {
      if (ALIASES[col] && !c.columns.includes(ALIASES[col])) { have.add(ALIASES[col]); out.aliases.push(`${col} → ${ALIASES[col]}`); }
      else have.add(col);
    }
    const specCols = st.fields.map((f) => f.name);
    out.missingColumns = specCols.filter((n) => !have.has(n));
    out.extraColumns = c.columns.filter((n) => !specCols.includes(n) && !(ALIASES[n] && specCols.includes(ALIASES[n])));
    if (c.rows === 0) issues.push({ level: "warn", text: "데이터 행이 없습니다 (헤더만)." });
    if (out.missingColumns.includes(st.pk)) issues.push({ level: "error", text: `기본키 컬럼 ${st.pk} 이(가) 없습니다.` });
    if (table !== "PERSON" && specCols.includes("person_id") && out.missingColumns.includes("person_id")) issues.push({ level: "error", text: "person_id 컬럼이 없습니다." });
    const otherMissing = out.missingColumns.filter((n) => n !== st.pk && n !== "person_id");
    if (otherMissing.length) issues.push({ level: "warn", text: `명세 컬럼 ${otherMissing.length}개 없음: ${otherMissing.slice(0, 6).join(", ")}${otherMissing.length > 6 ? " …" : ""}` });
    if (out.extraColumns.length) issues.push({ level: "info", text: `명세에 없는 컬럼 ${out.extraColumns.length}개 (무시됨): ${out.extraColumns.slice(0, 6).join(", ")}${out.extraColumns.length > 6 ? " …" : ""}` });
    for (const a of out.aliases) issues.push({ level: "info", text: `별칭 컬럼 해석: ${a}` });
    if (c.columns.some((n, i) => c.columns.indexOf(n) !== i)) issues.push({ level: "error", text: "중복된 컬럼명이 있습니다." });
    // 날짜 형식 표본
    const dateFields = st.fields.filter((f) => (f.type === "date" || f.type === "timestamp") && have.has(f.name));
    for (const f of dateFields) {
      const idx = c.columns.indexOf(f.name) >= 0 ? c.columns.indexOf(f.name) : c.columns.findIndex((n) => ALIASES[n] === f.name);
      if (idx < 0) continue;
      const bad = c.sample.map((r) => r[idx] ?? "").filter((v) => v !== "" && !(f.type === "date" ? DATE_RE : TS_RE).test(v));
      if (bad.length) { issues.push({ level: "warn", text: `${f.name} 날짜 형식이 다릅니다 (예: '${bad[0]}'). YYYY-MM-DD 여야 하며, 이대로면 타입 규칙에 걸립니다.` }); }
    }
    return out;
  });
}

export function buildPlan(cohort: string, tables: string[], spec: Spec, candidates: SourceCandidate[], mapping?: Record<string, string>): InputPlan {
  const auto = autoMatch(tables, spec, candidates);
  const m = mapping ?? auto;
  const checks = checkTables(tables, spec, candidates, m, auto);
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
  const rows: string[][] = parse(text, { to_line: limit + 1, relax_column_count: true, skip_empty_lines: true, delimiter: path.extname(c.path).toLowerCase() === ".tsv" ? "\t" : "," });
  return { columns: rows[0] ?? [], rows: rows.slice(1), total: c.rows };
}

// ------------------------------------------------------------------ 스테이징 (정규화된 입력 폴더)
/** 대응된 파일을 <TABLE>.csv (UTF-8) 로 옮긴다. 엑셀 시트는 CSV 로 변환하고, EUC-KR 은 UTF-8 로 바꾼다. */
export function stageInputs(candidates: SourceCandidate[], mapping: Record<string, string>, dir: string): void {
  fs.mkdirSync(dir, { recursive: true });
  const byId = new Map(candidates.map((c) => [c.id, c]));
  const opened = new Map<string, XLSX.WorkBook>();
  for (const [table, cid] of Object.entries(mapping)) {
    const c = byId.get(cid); if (!c || c.error) continue;
    const dest = path.join(dir, `${table}.csv`);
    if (c.kind === "xlsx" && c.sheet !== undefined) {
      let wb = opened.get(c.path);
      if (!wb) { wb = XLSX.readFile(c.path, { cellDates: true }); opened.set(c.path, wb); }
      const rows = sheetRows(wb.Sheets[c.sheet]);
      fs.writeFileSync(dest, rows.map((r) => r.map(csvCell).join(",")).join("\n") + "\n", "utf-8");
    } else {
      const { text, encoding } = readText(c.path);
      const delimiter = path.extname(c.path).toLowerCase() === ".tsv" ? "\t" : ",";
      if (encoding.name === "utf-8" && !encoding.bom && delimiter === ",") fs.copyFileSync(c.path, dest);
      else if (delimiter === ",") fs.writeFileSync(dest, text, "utf-8");
      else {
        const rows: string[][] = parse(text, { relax_column_count: true, skip_empty_lines: true, delimiter });
        fs.writeFileSync(dest, rows.map((r) => r.map(csvCell).join(",")).join("\n") + "\n", "utf-8");
      }
    }
  }
}

// ------------------------------------------------------------------ 입력 양식
function specRows(tables: string[], spec: Spec): (string | number | boolean)[][] {
  const rows: (string | number | boolean)[][] = [["테이블", "테이블(한글)", "순서", "컬럼", "타입", "필수", "키", "참조", "코드표", "범위", "패턴", "설명"]];
  for (const t of tables) {
    const st = spec.tables[t];
    st.fields.forEach((f, i) => {
      const range = Array.isArray(f.range) ? `${(f.range as number[])[0]} ~ ${(f.range as number[])[1]}` : "";
      rows.push([t, st.kor, i + 1, f.name, f.type, f.required ? "Y" : "", String(f.key ?? ""), String(f.ref ?? ""), String(f.codelist ?? ""), range, String(f.pattern ?? ""), String(f.desc ?? "")]);
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
