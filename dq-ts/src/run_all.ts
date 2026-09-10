// 전체 실행: 6개 코호트 × (clean, dirty) 검증 → 검출 성능 평가 → Python 참조와 비교
import path from "node:path";
import { getRoot } from "./load.js";
import { runEngine } from "./engine.js";
import { COHORTS, verify, writeVerificationSummary } from "./verify.js";
import { compareAll, printCompare } from "./compare.js";

const TODAY = process.env.KAI_TODAY ?? "2026-09-07"; // Python 참조 실행일과 맞춘다
const OUT = "output/reports";
const t0 = Date.now();
for (const c of COHORTS) for (const kind of ["clean", "dirty"]) {
  const s = await runEngine({ cohort: c, today: TODAY, data: path.join(getRoot(), `synth/output/${kind}/${c}`), out: path.join(OUT, `${kind}_${c}`) });
  console.log(`[${kind}_${c}] rules=${s.rules_total} failed=${s.rules_failed} skipped=${s.rules_skipped} error=${s.rules_error} violations=${s.violations_total}`);
}
console.log(`엔진 12회 실행: ${((Date.now() - t0) / 1000).toFixed(1)}s\n`);
const vs = COHORTS.map((c) => verify(c, OUT));
writeVerificationSummary(OUT, vs);
for (const v of vs) console.log(`[${v.cohort}] clean 오탐=${v.clean.violations} 주입=${v.faults_total} 검출=${v.faults_detected} 재현율=${v.recall} 유형 ${v.fault_types_fully_detected}/${v.fault_types}`);
console.log("");
const ok = printCompare(compareAll());
console.log(ok ? "\n동등성: 모든 실행에서 Python 참조 구현과 일치" : "\n동등성: 차이 있음");
process.exit(ok ? 0 : 1);
