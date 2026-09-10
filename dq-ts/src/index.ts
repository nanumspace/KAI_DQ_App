// 패키지 진입점 (Electron 앱 등 외부에서 쓰는 API)
export { Engine, runEngine, FINDING_COLUMNS } from "./engine.js";
export type { EngineOptions, Progress, ProgressFn, ProgressStage } from "./engine.js";
export { getRoot, setRoot, loadSpec, loadCodelists, loadConcepts, loadProfiles, loadStructuralRules, loadSemanticRules } from "./load.js";
export { readCsv, writeCsv, csvCell } from "./csv.js";
export { verify, writeVerificationSummary, COHORTS } from "./verify.js";
export type { Verification } from "./verify.js";
export { compareRun, compareAll } from "./compare.js";
export type * from "./types.js";
