// preload 가 노출한 API. 렌더러 전역에서 이것만 쓴다.
import type { Api } from "@shared/types";

export const api: Api = window.api;

export function fmt(n: number | null | undefined): string {
  if (n === null || n === undefined || Number.isNaN(n)) return "-";
  return Number(n).toLocaleString("ko-KR");
}

export function pct(n: number, digits = 2): string {
  return `${n.toFixed(digits)}%`;
}

export function fmtTime(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  const p = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}
