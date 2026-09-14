// 사용법: npm run engine -- --cohort LUNG_CANCER --data <csv 디렉터리> --out <보고서 디렉터리> [--today YYYY-MM-DD] [--spec v2]
import { parseArgs } from "node:util";
import { runEngine } from "./engine.js";

const { values } = parseArgs({
  options: { cohort: { type: "string" }, data: { type: "string" }, out: { type: "string" }, today: { type: "string" },
            spec: { type: "string" } },
});
if (!values.cohort || !values.data || !values.out) {
  console.error("필수 인자: --cohort --data --out [--today]");
  process.exit(2);
}
const spec = values.spec === "v2" ? "v2" : "v1";
const s = await runEngine({ cohort: values.cohort, data: values.data, out: values.out, today: values.today, spec });
console.log(`[${s.cohort}] rules=${s.rules_total} failed=${s.rules_failed} skipped=${s.rules_skipped} error=${s.rules_error} violations=${s.violations_total} (error=${s.violations_error}, warning=${s.violations_warning})`);
