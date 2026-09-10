// 회귀 시험: 6개 코호트 × (clean, dirty) 를 실행해
//   (1) clean 오탐 0, dirty 재현율 1.00
//   (2) Python 참조 구현(dq/reports)과 규칙 단위 결과·위반 행이 완전히 같음
// 을 확인한다. 규칙이나 엔진을 바꾼 뒤에는 이 시험이 기준선이다.
import { describe, it, expect, beforeAll } from "vitest";
import fs from "node:fs";
import path from "node:path";
import { getRoot } from "../src/load.js";
import { runEngine } from "../src/engine.js";
import { COHORTS, verify } from "../src/verify.js";
import { compareAll } from "../src/compare.js";

const OUT = path.join(getRoot(), "dq-ts/output/test-reports");
const TODAY = "2026-09-07";

beforeAll(async () => {
  fs.rmSync(OUT, { recursive: true, force: true });
  for (const c of COHORTS) for (const kind of ["clean", "dirty"]) {
    await runEngine({ cohort: c, today: TODAY, data: path.join(getRoot(), `synth/output/${kind}/${c}`), out: path.join(OUT, `${kind}_${c}`) });
  }
}, 120_000);

describe("검출 성능", () => {
  for (const c of COHORTS) {
    it(`${c}: clean 오탐 0, dirty 재현율 1.00`, () => {
      const v = verify(c, OUT);
      expect(v.clean.violations).toBe(0);
      expect(v.faults_detected).toBe(v.faults_total);
      expect(v.recall).toBe(1);
      expect(v.fault_types_fully_detected).toBe(v.fault_types);
    });
  }
});

describe("Python 참조 구현과 동등성", () => {
  const hasPy = fs.existsSync(path.join(getRoot(), "dq/reports/clean_LUNG_CANCER/summary.json"));
  it.skipIf(!hasPy)("12개 실행 모두 규칙 결과와 위반 행이 같다", () => {
    const results = compareAll(path.join(getRoot(), "dq/reports"), OUT);
    expect(results).toHaveLength(12);
    for (const r of results) {
      expect({ run: r.run, rule_diffs: r.rule_diffs, top_diffs: r.top_diffs, only_py: r.only_py, only_ts: r.only_ts })
        .toEqual({ run: r.run, rule_diffs: [], top_diffs: [], only_py: [], only_ts: [] });
    }
  });
});
