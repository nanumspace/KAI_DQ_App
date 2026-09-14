// 서식 → 레코드 변환 시험.
//
// 확장 저장 서식은 서식 한 행이 확장 테이블 한 행이므로 **왕복**으로 확인할 수 있다.
// 생성된 저장 CSV 에서 concept_id 를 코드로 되돌려 서식을 만들고, 그 서식을 다시 변환해
// 원래 저장 CSV 와 같은 값이 나오는지 본다. 중간에 코드↔concept_id 짝이 어긋나면 여기서 걸린다.
//
// OMOP 투영 서식은 되돌릴 수 없으므로(한 행이 여러 테이블로 흩어진다) 만들어진 레코드의
// 모양만 확인한다 — 어느 테이블에 앉는지, 필수 자리가 채워지는지.
import { describe, it, expect } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { getRoot } from "../src/load.js";
import { readCsv } from "../src/csv.js";
import { loadCrfSpec, CrfConverter, formsForCohort } from "../src/crf.js";

const COHORT = "LUNG_CANCER";
const dataDir = path.join(getRoot(), `synth/output/clean_v2/${COHORT}`);
const hasData = fs.existsSync(dataDir);

/** concept_id → 값 집합 코드 (CONCEPT_SET_ITEM.csv) */
function codeOfConcept(): Map<string, string> {
  const p = path.join(getRoot(), "spec/v2/vocab/CONCEPT_SET_ITEM.csv");
  const out = new Map<string, string>();
  for (const line of fs.readFileSync(p, "utf-8").split(/\r?\n/).slice(1)) {
    if (!line.trim()) continue;
    const [, conceptId, code] = line.split(",");
    if (conceptId) out.set(conceptId, code ?? "");
  }
  return out;
}

describe("서식 → 레코드 변환", () => {
  const spec = loadCrfSpec();

  it("폐암 서식 목록이 확장 저장과 OMOP 투영 두 종류로 나뉜다", () => {
    const forms = formsForCohort(spec, COHORT);
    expect(forms.length).toBeGreaterThan(0);
    expect(forms.some((f) => f.mapping)).toBe(true);    // 투영
    expect(forms.some((f) => !f.mapping)).toBe(true);   // 확장 저장
  });

  it.skipIf(!hasData)("확장 저장 서식은 왕복해도 값이 같다 (PATHOLOGY_REPORT)", () => {
    const table = readCsv(path.join(dataDir, "PATHOLOGY_REPORT.csv"));
    const form = spec.forms["PATHOLOGY_REPORT"];
    const toCode = codeOfConcept();

    // 저장 CSV → 서식 행 (concept_id 를 사람이 고르는 코드로 되돌린다)
    const rows: Array<Record<string, string>> = [];
    for (let i = 0; i < Math.min(table.n, 20); i++) {
      const row: Record<string, string> = {};
      for (const f of form.fields) {
        const col = f.target?.column;
        if (!col || !table.cols.has(col)) continue;
        const v = table.cols.get(col)![i];
        if (v === "") continue;
        row[f.name] = col.endsWith("_concept_id") ? (toCode.get(v) ?? v) : v;
      }
      if (row["person_id"]) rows.push(row);
    }
    expect(rows.length).toBeGreaterThan(0);

    const conv = new CrfConverter(spec, COHORT, 1);
    conv.convertForm(form, rows);
    const { records, issues } = conv.result();
    const out = records.get("PATHOLOGY_REPORT")!;
    expect(out).toHaveLength(rows.length);
    expect(issues.filter((x) => x.message.includes("값 집합"))).toHaveLength(0);

    // 값 집합을 쓰는 컬럼이 원래 concept_id 로 돌아왔는지
    for (let i = 0; i < rows.length; i++) {
      for (const f of form.fields) {
        const col = f.target?.column;
        if (!col || !col.endsWith("_concept_id") || !f.codelist) continue;
        const orig = table.cols.get(col)?.[i] ?? "";
        if (orig === "") continue;
        expect(out[i][col], `${col} 이 왕복에서 달라졌다`).toBe(orig);
        expect(out[i][col.replace(/_concept_id$/, "_source_value")]).toBe(toCode.get(orig));
      }
    }
  });

  it("OMOP 투영 서식 한 행이 여러 테이블로 흩어진다 (STAGING)", () => {
    const conv = new CrfConverter(spec, COHORT, 1);
    conv.convertForm(spec.forms["STAGING"], [{
      person_id: "100001", staging_date: "2022-03-27",
      initial_clinical_stage: "IV", clinical_tnm: "cT2aN2M1b",
    }]);
    const { records } = conv.result();
    const meas = records.get("MEASUREMENT") ?? [];
    expect(meas.length).toBeGreaterThan(0);
    for (const r of meas) {
      expect(r["person_id"]).toBe("100001");
      expect(r["measurement_date"]).toBe("2022-03-27");
      expect(r["measurement_concept_id"]).toBeTruthy();
      expect(r["measurement_id"]).toBeTruthy();
    }
  });

  it("person_id 가 없으면 그 행은 버리고 이유를 남긴다", () => {
    const conv = new CrfConverter(spec, COHORT, 1);
    conv.convertForm(spec.forms["STAGING"], [{ staging_date: "2022-03-27", initial_clinical_stage: "IV" }]);
    const { records, issues } = conv.result();
    expect(records.size).toBe(0);
    expect(issues[0].field).toBe("person_id");
  });
});
