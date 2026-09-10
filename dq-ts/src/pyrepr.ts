// Python repr 흉내. detail 문자열을 참조 구현과 글자 단위로 맞추기 위해 쓴다.

export function pyStr(s: string): string {
  if (s.includes("'") && !s.includes('"')) return `"${s}"`;
  return `'${s.replace(/\\/g, "\\\\").replace(/'/g, "\\'")}'`;
}

export function pyList(items: string[]): string {
  return `[${items.map(pyStr).join(", ")}]`;
}

/** 파이썬 sorted() 와 같은 코드포인트 순 정렬 */
export function pySorted(items: Iterable<string>): string[] {
  return [...items].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}
