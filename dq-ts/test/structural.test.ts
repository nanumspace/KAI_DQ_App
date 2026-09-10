// 구조 검사 보조 함수의 단위 시험 (참조 구현의 pandas 동작과 같은지)
import { describe, it, expect } from "vitest";
import { validDate, validTimestamp, parseIsoDate, parseNum, INT_RE, FLOAT_RE } from "../src/structural.js";
import { pyList, pyStr, pySorted } from "../src/pyrepr.js";
import { csvCell } from "../src/csv.js";

describe("날짜 판정", () => {
  it("달력에 있는 날짜만 유효", () => {
    expect(validDate("2024-02-29")).toBe(true);
    expect(validDate("2023-02-29")).toBe(false);
    expect(validDate("2023-02-30")).toBe(false);
    expect(validDate("2024/13/40")).toBe(false);
    expect(validDate("20240101")).toBe(false);
    expect(validDate("2024-1-5")).toBe(false);
  });
  it("타임스탬프는 시분초 범위까지 본다", () => {
    expect(validTimestamp("2024-01-05")).toBe(true);
    expect(validTimestamp("2024-01-05 10:30")).toBe(true);
    expect(validTimestamp("2024-01-05T10:30:15.5")).toBe(true);
    expect(validTimestamp("2024-01-05 24:00")).toBe(false);
    expect(validTimestamp("2024-01-05 10:60")).toBe(false);
  });
  it("epoch 변환", () => {
    expect(parseIsoDate("2026-09-07")).toBe(Date.UTC(2026, 8, 7));
    expect(parseIsoDate("2026-09-07 12:00:00")).toBe(Date.UTC(2026, 8, 7, 12));
    expect(parseIsoDate("bad")).toBeNull();
  });
});

describe("수치 판정", () => {
  it("정수/실수 정규식", () => {
    expect(INT_RE.test("-12")).toBe(true);
    expect(INT_RE.test("12.0")).toBe(false);
    expect(FLOAT_RE.test("12.0")).toBe(true);
    expect(FLOAT_RE.test(".5")).toBe(true);
    expect(FLOAT_RE.test("1e3")).toBe(true);
    expect(FLOAT_RE.test("N/A")).toBe(false);
  });
  it("to_numeric(coerce) 대응", () => {
    expect(parseNum("")).toBeNull();
    expect(parseNum("N/A")).toBeNull();
    expect(parseNum("70.5")).toBe(70.5);
  });
});

describe("Python repr 흉내", () => {
  it("리스트와 문자열", () => {
    expect(pyList(["a", "b"])).toBe("['a', 'b']");
    expect(pyStr("it's")).toBe('"it\'s"');
    expect(pySorted(["b", "a", "B"])).toEqual(["B", "a", "b"]);
  });
});

describe("CSV 인용", () => {
  it("쉼표·따옴표·줄바꿈이 있을 때만 인용", () => {
    expect(csvCell("abc")).toBe("abc");
    expect(csvCell("a,b")).toBe('"a,b"');
    expect(csvCell('say "hi"')).toBe('"say ""hi"""');
    expect(csvCell(null)).toBe("");
  });
});
