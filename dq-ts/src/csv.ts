// CSV 읽기/쓰기. pandas read_csv(dtype=str, keep_default_na=False) 와 같은 의미:
// 모든 값은 문자열 그대로, 빈 칸은 빈 문자열, 컬럼명은 양끝 공백 제거.
import fs from "node:fs";
import { parse } from "csv-parse/sync";
import type { RawTable } from "./types.js";

export function readCsv(p: string): RawTable {
  const text = fs.readFileSync(p, "utf-8");
  const rows: string[][] = parse(text, { bom: true, relax_column_count: false, skip_empty_lines: true });
  if (rows.length === 0) return { columns: [], cols: new Map(), n: 0 };
  const columns = rows[0].map((c) => c.trim());
  const cols = new Map<string, string[]>();
  columns.forEach((c, j) => {
    const arr = new Array<string>(rows.length - 1);
    for (let i = 1; i < rows.length; i++) arr[i - 1] = rows[i][j] ?? "";
    cols.set(c, arr);
  });
  return { columns, cols, n: rows.length - 1 };
}

/** pandas to_csv 의 최소 인용(QUOTE_MINIMAL)과 같은 규칙으로 한 칸을 인용한다. */
export function csvCell(v: unknown): string {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\r\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

export function writeCsv(p: string, columns: string[], rows: Record<string, unknown>[], bom = true): void {
  const lines = [columns.map(csvCell).join(",")];
  for (const r of rows) lines.push(columns.map((c) => csvCell(r[c])).join(","));
  fs.writeFileSync(p, (bom ? "\uFEFF" : "") + lines.join("\n") + "\n", "utf-8");
}
