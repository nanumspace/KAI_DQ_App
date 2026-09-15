// 실데이터 흉내 입력 시험.
//
// 가상데이터는 우리가 만든 것이라 늘 단정하다. 병원이 내보낸 파일은 그렇지 않다 —
// 엑셀이 붙인 BOM, SQL 도구가 붙인 00:00:00, pandas 가 남긴 100001.0, 대문자 헤더,
// 'NULL' 이라는 글자, 세미콜론 구분자. 이런 것이 들어와도 프로그램이 죽지 않고
// (1) 내보내기 흔적이면 조용히 바로잡되 무엇을 바로잡았는지 말하고
// (2) 진짜 데이터 문제면 규칙 위반으로 보고해야 한다.
//
// 깨끗한 폐암 v2 데이터를 여러 가지로 망가뜨려 입력 처리(인식 → 대응 → 사전 점검 → 정규화)와
// 엔진을 차례로 통과시킨다. '흔적' 계열은 원본과 같은 결과(위반 0)가 나와야 하고,
// '문제' 계열은 특정 규칙이 울려야 한다.
import { describe, it, expect, beforeAll } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { execFileSync } from "node:child_process";
import * as XLSX from "xlsx";
import { setRoot, loadSpecV2, loadProfilesV2, runEngine } from "@engine/index.js";
import type { Spec } from "@engine/types.js";
import { inspectPaths, buildPlan, stageInputs } from "../src/main/input";

const ROOT = path.resolve(__dirname, "../..");
const COHORT = "LUNG_CANCER";
const SRC = path.join(ROOT, "synth/output/clean_v2", COHORT);
const hasData = fs.existsSync(path.join(SRC, "PERSON.csv"));
const TODAY = "2026-09-07";

let work: string;
let spec: Spec;
let tables: string[];

beforeAll(() => {
  setRoot(ROOT);
  spec = loadSpecV2();
  const p = loadProfilesV2()[COHORT];
  tables = [...p.omop_tables, ...p.extension_tables];
  work = fs.mkdtempSync(path.join(os.tmpdir(), "kai-realworld-"));
});

// ---------------------------------------------------------------- 도구
function copyClean(name: string): string {
  const d = path.join(work, name);
  fs.mkdirSync(d, { recursive: true });
  for (const t of tables) {
    const f = path.join(SRC, `${t}.csv`);
    if (fs.existsSync(f)) fs.copyFileSync(f, path.join(d, `${t}.csv`));
  }
  return d;
}

function read(d: string, t: string): string { return fs.readFileSync(path.join(d, `${t}.csv`), "utf-8"); }
function write(d: string, t: string, text: string | Buffer): void { fs.writeFileSync(path.join(d, `${t}.csv`), text); }

/** 입력 처리 전 구간을 돌리고 정규화된 폴더와 사전 점검 결과를 돌려준다 */
function stage(inputs: string[], name: string) {
  const candidates = inspectPaths(inputs);
  const plan = buildPlan(COHORT, tables, spec, candidates, undefined, ["PERSON"]);
  const staged = path.join(work, `${name}-staged`);
  const norm = stageInputs(plan.candidates, plan.mapping, staged, spec);
  return { plan, staged, norm };
}

async function validate(dataDir: string, name: string) {
  const out = path.join(work, `${name}-out`);
  const s = await runEngine({ cohort: COHORT, today: TODAY, spec: "v2", data: dataDir, out });
  const findings = fs.readFileSync(path.join(out, "findings.csv"), "utf-8").split(/\r?\n/).filter(Boolean).slice(1);
  return { summary: s, findings };
}

const issuesOf = (plan: ReturnType<typeof buildPlan>, table: string) => plan.tables.find((t) => t.table === table)?.issues.map((i) => i.text) ?? [];

// ---------------------------------------------------------------- 기준: 원본은 위반 0
describe.skipIf(!hasData)("실데이터 흉내 입력", () => {
  it("원본 그대로: 위반 0 (이 시험의 기준)", async () => {
    const d = copyClean("pristine");
    const { plan, staged } = stage([d], "pristine");
    expect(plan.ok).toBe(true);
    expect(Object.keys(plan.mapping)).toHaveLength(tables.length);
    const { summary } = await validate(staged, "pristine");
    expect(summary.violations_total).toBe(0);
  });

  // -------------------------------------------------------------- 내보내기 흔적: 조용히 바로잡고 말한다
  it("UTF-8 BOM · CRLF 줄끝: 원본과 같다", async () => {
    const d = copyClean("bom-crlf");
    for (const t of tables) write(d, t, "\uFEFF" + read(d, t).replace(/\r?\n/g, "\r\n"));
    const { plan, staged } = stage([d], "bom-crlf");
    expect(plan.ok).toBe(true);
    expect((await validate(staged, "bom-crlf")).summary.violations_total).toBe(0);
  });

  it("EUC-KR 인코딩 (한글 노트 포함): 변환되어 원본과 같다", async () => {
    const d = copyClean("euckr");
    // Node 에는 EUC-KR 인코더가 없다. python 의 cp949 로 NOTE(한글 본문)를 다시 쓴다. python 이 없으면 건너뛴다.
    let py = false;
    try { execFileSync("python3", ["-c", "import sys; t=open(sys.argv[1],encoding='utf-8').read(); open(sys.argv[1],'wb').write(t.encode('cp949'))", path.join(d, "NOTE.csv")]); py = true; } catch { /* python 없음 */ }
    if (!py) return;
    const { plan, staged } = stage([d], "euckr");
    expect(plan.ok).toBe(true);
    expect(plan.candidates.find((c) => c.name === "NOTE.csv")?.encoding).toContain("EUC-KR");
    expect((await validate(staged, "euckr")).summary.violations_total).toBe(0);
  });

  it("대문자 헤더 (Oracle · SQL Server 내보내기): 소문자로 맞추고 알린다", async () => {
    const d = copyClean("upper");
    for (const t of tables) {
      const lines = read(d, t).split("\n");
      lines[0] = lines[0].toUpperCase();
      write(d, t, lines.join("\n"));
    }
    const { plan, staged } = stage([d], "upper");
    expect(plan.ok).toBe(true);
    expect(issuesOf(plan, "PERSON").some((s) => s.includes("대소문자"))).toBe(true);
    expect((await validate(staged, "upper")).summary.violations_total).toBe(0);
  });

  it("헤더와 값의 앞뒤 공백: 걷어 내고 원본과 같다", async () => {
    const d = copyClean("spaces");
    const t = "VISIT_OCCURRENCE";
    const lines = read(d, t).split("\n");
    lines[0] = lines[0].split(",").map((c) => ` ${c} `).join(",");
    for (let i = 1; i < lines.length; i++) if (lines[i]) lines[i] = lines[i].split(",").map((c) => (c ? ` ${c} ` : c)).join(",");
    write(d, t, lines.join("\n"));
    const { plan, staged, norm } = stage([d], "spaces");
    expect(plan.ok).toBe(true);
    expect(norm[t]?.trimmed ?? 0).toBeGreaterThan(0);
    expect((await validate(staged, "spaces")).summary.violations_total).toBe(0);
  });

  it("'NULL' · 'NA' · 'N/A' 글자: 빈 값으로 바꾸고 몇 개인지 말한다", async () => {
    const d = copyClean("nulls");
    const t = "DEATH";
    const lines = read(d, t).split("\n");
    const cols = lines[0].split(",");
    const j = cols.indexOf("cause_concept_id");
    expect(j).toBeGreaterThan(-1);
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i]) continue;
      const cells = lines[i].split(",");
      if (cells[j] === "") cells[j] = ["NULL", "null", "NA", "N/A"][i % 4];
      lines[i] = cells.join(",");
    }
    write(d, t, lines.join("\n"));
    const { plan, staged, norm } = stage([d], "nulls");
    expect(plan.ok).toBe(true);
    expect(issuesOf(plan, t).some((s) => s.includes("NULL"))).toBe(true);
    expect(norm[t]?.nullStrings ?? 0).toBeGreaterThan(0);
    expect((await validate(staged, "nulls")).summary.violations_total).toBe(0);
  });

  it("정수에 붙은 .0 (pandas · 엑셀): 정수 컬럼에서만 걷어 내고 원본과 같다", async () => {
    const d = copyClean("float-ids");
    for (const t of ["PERSON", "VISIT_OCCURRENCE", "CONDITION_OCCURRENCE"]) {
      const lines = read(d, t).split("\n");
      const cols = lines[0].split(",");
      const intCols = new Set(spec.tables[t].fields.filter((f) => f.type === "integer" || f.type === "bigint").map((f) => f.name));
      for (let i = 1; i < lines.length; i++) {
        if (!lines[i]) continue;
        const cells = lines[i].split(",");
        cols.forEach((c, k) => { if (intCols.has(c) && cells[k] && /^\d+$/.test(cells[k])) cells[k] = `${cells[k]}.0`; });
        lines[i] = cells.join(",");
      }
      write(d, t, lines.join("\n"));
    }
    const { plan, staged, norm } = stage([d], "float-ids");
    expect(plan.ok).toBe(true);
    expect(norm["PERSON"]?.intFloats ?? 0).toBeGreaterThan(0);
    // 참조무결성이 유지되어야 한다: PERSON 의 100001.0 과 VISIT 의 100001.0 이 같은 사람으로 남는다
    expect((await validate(staged, "float-ids")).summary.violations_total).toBe(0);
  });

  it("날짜에 붙은 00:00:00 (SQL 내보내기): 날짜 컬럼에서만 걷어 내고 원본과 같다", async () => {
    const d = copyClean("zero-time");
    const t = "CONDITION_OCCURRENCE";
    const lines = read(d, t).split("\n");
    const cols = lines[0].split(",");
    const dateCols = new Set(spec.tables[t].fields.filter((f) => f.type === "date").map((f) => f.name));
    for (let i = 1; i < lines.length; i++) {
      if (!lines[i]) continue;
      const cells = lines[i].split(",");
      cols.forEach((c, k) => { if (dateCols.has(c) && /^\d{4}-\d{2}-\d{2}$/.test(cells[k])) cells[k] = `${cells[k]} 00:00:00`; });
      lines[i] = cells.join(",");
    }
    write(d, t, lines.join("\n"));
    const { plan, staged, norm } = stage([d], "zero-time");
    expect(plan.ok).toBe(true);
    expect(norm[t]?.zeroTimes ?? 0).toBeGreaterThan(0);
    expect((await validate(staged, "zero-time")).summary.violations_total).toBe(0);
  });

  it("세미콜론 구분자 (유럽식 엑셀 CSV): 구분자를 알아채고 원본과 같다", async () => {
    const d = copyClean("semicolon");
    // NOTE 는 본문에 쉼표가 있어 인용이 얽힌다. 숫자와 날짜만 있는 표로 본다.
    const t = "OBSERVATION_PERIOD";
    write(d, t, read(d, t).split("\n").map((l) => l.replace(/,/g, ";")).join("\n"));
    const { plan, staged } = stage([d], "semicolon");
    expect(plan.ok).toBe(true);
    expect(plan.tables.find((x) => x.table === t)?.missingColumns).toEqual([]);
    expect((await validate(staged, "semicolon")).summary.violations_total).toBe(0);
  });

  it("끝에 붙은 빈 컬럼 (엑셀 저장 흔적 ',,,'): 버리고 원본과 같다", async () => {
    const d = copyClean("trailing");
    const t = "PROCEDURE_OCCURRENCE";
    write(d, t, read(d, t).split("\n").map((l) => (l ? `${l},,` : l)).join("\n"));
    const { plan, staged } = stage([d], "trailing");
    expect(plan.ok).toBe(true);
    expect(plan.tables.find((x) => x.table === t)?.extraColumns).toEqual([]);
    expect((await validate(staged, "trailing")).summary.violations_total).toBe(0);
  });

  it("파일 이름이 다름 (person_20260901.csv · 소문자): 자동 대응된다", async () => {
    const d = copyClean("names");
    fs.renameSync(path.join(d, "PERSON.csv"), path.join(d, "person_20260901.csv"));
    fs.renameSync(path.join(d, "VISIT_OCCURRENCE.csv"), path.join(d, "visit_occurrence.csv"));
    const { plan } = stage([d], "names");
    expect(plan.ok).toBe(true);
    expect(Object.keys(plan.mapping)).toHaveLength(tables.length);
  });

  it("따옴표 안의 줄바꿈과 쉼표 (NOTE 본문): 행이 깨지지 않는다", async () => {
    const d = copyClean("quoted");
    const t = "NOTE";
    const lines = read(d, t).split("\n");
    const cols = lines[0].split(",");
    const j = cols.indexOf("note_text");
    // 첫 데이터 행의 본문을 줄바꿈·쉼표·따옴표가 든 것으로 바꾼다 (원본 값이 인용돼 있을 수 있어 행 전체를 다시 만든다)
    const first = lines[1].split(",");   // 원본은 본문에 쉼표가 없는 행이라고 가정하지 않는다 → 아래에서 확인
    if (first.length === cols.length) {
      first[j] = '"1일차: 흉통, ""좌측"" \n2일차: 호전"';
      lines[1] = first.join(",");
      write(d, t, lines.join("\n"));
    }
    const { plan, staged } = stage([d], "quoted");
    expect(plan.ok).toBe(true);
    const r = await validate(staged, "quoted");
    expect(r.summary.violations_total).toBe(0);
  });

  // -------------------------------------------------------------- 진짜 문제: 규칙이 울려야 한다
  it("엑셀 일련번호 날짜 (45000) 가 CSV 에 남음: 날짜 타입 위반으로 보고된다", async () => {
    const d = copyClean("serial-dates");
    const t = "VISIT_OCCURRENCE";
    const lines = read(d, t).split("\n");
    const cols = lines[0].split(",");
    const j = cols.indexOf("visit_start_date");
    for (let i = 1; i < Math.min(lines.length, 6); i++) { const c = lines[i].split(","); c[j] = "45000"; lines[i] = c.join(","); }
    write(d, t, lines.join("\n"));
    const { plan, staged } = stage([d], "serial-dates");
    expect(plan.ok).toBe(true);   // 막지는 않는다
    expect(issuesOf(plan, t).some((s) => s.includes("날짜 형식"))).toBe(true);   // 미리 알려는 준다
    const r = await validate(staged, "serial-dates");
    expect(r.findings.some((l) => l.includes("visit_start_date") && /타입|date/.test(l))).toBe(true);
  });

  it("천 단위 쉼표 (\"1,234\"): 숫자 타입 위반으로 보고된다", async () => {
    const d = copyClean("thousands");
    const t = "MEASUREMENT";
    const lines = read(d, t).split("\n");
    const cols = lines[0].split(",");
    const j = cols.indexOf("value_as_number");
    let changed = 0;
    for (let i = 1; i < lines.length && changed < 5; i++) {
      const c = lines[i].split(",");
      if (c.length === cols.length && /^\d{4,}(\.\d+)?$/.test(c[j])) { c[j] = `"${Number(c[j]).toLocaleString("en-US")}"`; lines[i] = c.join(","); changed++; }
    }
    if (changed === 0) return;   // 네 자리 이상 값이 없으면 볼 것이 없다
    write(d, t, lines.join("\n"));
    const { staged } = stage([d], "thousands");
    const r = await validate(staged, "thousands");
    expect(r.findings.filter((l) => l.includes("value_as_number")).length).toBeGreaterThanOrEqual(changed);
  });

  it("중복된 헤더: 사전 점검이 오류로 막는다", () => {
    const d = copyClean("dup-header");
    const t = "PERSON";
    const lines = read(d, t).split("\n");
    lines[0] = lines[0] + ",person_id";
    write(d, t, lines.map((l, i) => (i > 0 && l ? `${l},` : l)).join("\n"));
    const { plan } = stage([d], "dup-header");
    expect(plan.ok).toBe(false);
    expect(issuesOf(plan, t).some((s) => s.includes("중복된 컬럼명"))).toBe(true);
  });

  it("빈 파일 (0 바이트) · UTF-16 파일: 죽지 않고 읽기 실패로 보고한다", () => {
    const d = copyClean("bad-files");
    write(d, "DEATH", "");
    write(d, "SPECIMEN", Buffer.from("\uFEFF" + read(d, "SPECIMEN"), "utf16le"));
    const { plan } = stage([d], "bad-files");
    const death = plan.tables.find((t) => t.table === "DEATH")!;
    const spec_ = plan.tables.find((t) => t.table === "SPECIMEN")!;
    expect(death.issues.some((i) => i.level === "error" || i.level === "warn")).toBe(true);
    expect(spec_.issues.some((i) => i.level === "error")).toBe(true);
  });

  it("앞자리 0 이 있는 ID (000123): 표들 사이에서 일관되면 위반이 아니다", async () => {
    const d = copyClean("leading-zero");
    for (const t of tables) {
      if (!fs.existsSync(path.join(d, `${t}.csv`))) continue;
      const lines = read(d, t).split("\n");
      const cols = lines[0].split(",");
      const j = cols.indexOf("person_id");
      if (j < 0) continue;
      for (let i = 1; i < lines.length; i++) {
        if (!lines[i]) continue;
        const c = lines[i].split(",");
        if (c.length === cols.length && /^\d+$/.test(c[j])) { c[j] = `00${c[j]}`; lines[i] = c.join(","); }
      }
      write(d, t, lines.join("\n"));
    }
    const { staged } = stage([d], "leading-zero");
    const r = await validate(staged, "leading-zero");
    expect(r.findings.filter((l) => l.includes("person_id")).length).toBe(0);
  });

  // -------------------------------------------------------------- 엑셀 경로
  it("엑셀 한 파일 (시트당 테이블, 날짜 셀 · 숫자 셀): 원본과 같다", async () => {
    const d = copyClean("xlsx-src");
    const wb = XLSX.utils.book_new();
    for (const t of tables) {
      const f = path.join(d, `${t}.csv`);
      if (!fs.existsSync(f)) continue;
      const rows = read(d, t).split("\n").filter(Boolean).map((l) => l.split(","));
      // NOTE 본문은 쉼표가 들어 split 이 안 맞을 수 있다 → 그 표는 건너뛴다(빈 시트로)
      const ok = rows.every((r) => r.length === rows[0].length);
      const ws = XLSX.utils.aoa_to_sheet(ok ? rows.map((r, i) => (i === 0 ? r : r.map((v) => (/^\d+$/.test(v) && v.length < 15 ? Number(v) : v)))) : [rows[0]]);
      XLSX.utils.book_append_sheet(wb, ws, t.slice(0, 31));
    }
    const file = path.join(work, "cohort.xlsx");
    XLSX.writeFile(wb, file);
    const { plan, staged } = stage([file], "xlsx");
    expect(plan.ok).toBe(true);
    const r = await validate(staged, "xlsx");
    // 숫자 셀로 넣은 ID 가 '100001' 로 돌아오고 참조가 깨지지 않아야 한다
    expect(r.findings.filter((l) => /person_id|_id/.test(l) && /참조|타입/.test(l)).length).toBe(0);
  });
});
