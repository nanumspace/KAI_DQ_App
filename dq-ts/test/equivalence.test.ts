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

// ---------------------------------------------------------------- v2 경로
// v2 도 6개 코호트를 모두 돌려, Python 참조 구현과 위반 행까지 같은지 본다.
// 두 구현이 갈라지면 여기서 먼저 걸린다(실제로 위반 0 일 때 머리글 처리가 달랐던 것을 이 시험이 잡았다).
describe("v2: Python 참조 구현과 동등성", () => {
  const v2Out = path.join(getRoot(), "dq-ts/output/test-reports-v2");
  const pyDir = (kind: string, cohort: string) => path.join(getRoot(), `dq/reports/${kind}_v2_${cohort}`);
  const dataDir = (kind: string, cohort: string) => path.join(getRoot(), `synth/output/${kind}_v2/${cohort}`);
  // 데이터와 Python 보고서가 둘 다 있는 코호트만 본다(아직 안 만든 것은 건너뛴다).
  const ready = COHORTS.filter((c) =>
    fs.existsSync(dataDir("clean", c)) && fs.existsSync(path.join(pyDir("clean", c), "summary.json")));

  beforeAll(async () => {
    fs.rmSync(v2Out, { recursive: true, force: true });
    for (const c of ready) for (const kind of ["clean", "dirty"]) {
      if (!fs.existsSync(dataDir(kind, c))) continue;
      await runEngine({ cohort: c, today: TODAY, spec: "v2", data: dataDir(kind, c), out: path.join(v2Out, `${kind}_${c}`) });
    }
  }, 300_000);

  it("6개 코호트가 모두 v2 로 옮겨져 있다", () => {
    expect(ready).toEqual(COHORTS);
  });

  for (const c of COHORTS) {
    it(`${c}: clean·dirty 의 보고서(report.md)가 Python 과 같다 — 예시의 값 가리기까지`, () => {
      for (const kind of ["clean", "dirty"]) {
        const py = path.join(pyDir(kind, c), "report.md");
        const ts = path.join(v2Out, `${kind}_${c}`, "report.md");
        if (!fs.existsSync(py) || !fs.existsSync(ts)) continue;
        expect(fs.readFileSync(ts, "utf-8"), `${c} ${kind} 의 report.md 가 Python 과 다르다`).toBe(fs.readFileSync(py, "utf-8"));
      }
    });

    it(`${c}: clean·dirty 의 위반 행이 Python 과 같다`, () => {
      const norm = (p: string) => fs.readFileSync(p, "utf-8").replace(/^\uFEFF/, "").split(/\r?\n/).filter(Boolean).sort();
      let compared = 0;
      for (const kind of ["clean", "dirty"]) {
        const py = path.join(pyDir(kind, c), "findings.csv");
        const ts = path.join(v2Out, `${kind}_${c}`, "findings.csv");
        if (!fs.existsSync(py) || !fs.existsSync(ts)) continue;
        expect(norm(ts), `${c} ${kind} 의 위반 행이 Python 과 다르다`).toEqual(norm(py));
        compared += 1;
      }
      expect(compared, `${c} 를 대조할 보고서가 없다`).toBe(2);
    });
  }

  it("깨끗한 데이터에서는 어느 코호트도 위반이 없다", () => {
    for (const c of ready) {
      const p = path.join(v2Out, `clean_${c}`, "findings.csv");
      const rows = fs.readFileSync(p, "utf-8").split(/\r?\n/).filter(Boolean);
      expect(rows.length, `${c} 의 깨끗한 데이터에 위반이 있다`).toBe(1);   // 머리글 한 줄만
    }
  });
});

// ---------------------------------------------------------------- v3 경로
// v3(의뢰사 9/30 매뉴얼 + 10/01 검토 결정)도 6개 코호트를 모두 돌려 Python 과 보고서·위반 행까지 같은지 본다.
// v3 는 v1 과 같은 '질환별 표' 모양이라 v1 코드 경로를 다른 파일로 돈다. 생성은 `python dq/run_all.py --spec v3`.
describe("v3: Python 참조 구현과 동등성", () => {
  const v3Out = path.join(getRoot(), "dq-ts/output/test-reports-v3");
  const pyDir = (kind: string, cohort: string) => path.join(getRoot(), `dq/reports/${kind}_v3_${cohort}`);
  const dataDir = (kind: string, cohort: string) => path.join(getRoot(), `synth/output/${kind}_v3/${cohort}`);
  const ready = COHORTS.filter((c) =>
    fs.existsSync(dataDir("clean", c)) && fs.existsSync(path.join(pyDir("clean", c), "summary.json")));

  beforeAll(async () => {
    fs.rmSync(v3Out, { recursive: true, force: true });
    for (const c of ready) for (const kind of ["clean", "dirty"]) {
      if (!fs.existsSync(dataDir(kind, c))) continue;
      await runEngine({ cohort: c, today: TODAY, spec: "v3", data: dataDir(kind, c), out: path.join(v3Out, `${kind}_${c}`) });
    }
  }, 300_000);

  it("6개 코호트가 모두 v3 샘플 데이터와 Python 보고서를 갖고 있다", () => {
    expect(ready).toEqual(COHORTS);
  });

  for (const c of COHORTS) {
    it(`${c}: clean·dirty 의 보고서(report.md)가 Python 과 같다`, () => {
      for (const kind of ["clean", "dirty"]) {
        const py = path.join(pyDir(kind, c), "report.md");
        const ts = path.join(v3Out, `${kind}_${c}`, "report.md");
        if (!fs.existsSync(py) || !fs.existsSync(ts)) continue;
        expect(fs.readFileSync(ts, "utf-8"), `${c} ${kind} 의 report.md 가 Python 과 다르다`).toBe(fs.readFileSync(py, "utf-8"));
      }
    });

    it(`${c}: clean·dirty 의 위반 행이 Python 과 같다`, () => {
      const norm = (p: string) => fs.readFileSync(p, "utf-8").replace(/^\uFEFF/, "").split(/\r?\n/).filter(Boolean).sort();
      let compared = 0;
      for (const kind of ["clean", "dirty"]) {
        const py = path.join(pyDir(kind, c), "findings.csv");
        const ts = path.join(v3Out, `${kind}_${c}`, "findings.csv");
        if (!fs.existsSync(py) || !fs.existsSync(ts)) continue;
        expect(norm(ts), `${c} ${kind} 의 위반 행이 Python 과 다르다`).toEqual(norm(py));
        compared += 1;
      }
      expect(compared, `${c} 를 대조할 보고서가 없다`).toBe(2);
    });
  }

  it("깨끗한 데이터에서는 어느 코호트도 위반이 없다", () => {
    for (const c of ready) {
      const p = path.join(v3Out, `clean_${c}`, "findings.csv");
      const rows = fs.readFileSync(p, "utf-8").split(/\r?\n/).filter(Boolean);
      expect(rows.length, `${c} 의 깨끗한 데이터에 위반이 있다`).toBe(1);   // 머리글 한 줄만
    }
  });
});
