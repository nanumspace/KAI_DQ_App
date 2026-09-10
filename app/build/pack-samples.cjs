// 견본 데이터 묶음 생성: synth/output/{clean,dirty}/<COHORT>/ 를 코호트·종류별 zip 으로 만든다.
// 각 zip 에는 <TABLE>.csv, (dirty) fault_manifest.csv, README.txt 가 폴더 바로 아래에, 시트당 테이블 하나인 엑셀 파일이 excel/ 에 들어간다.
// 앱은 끌어다 놓은 폴더의 바로 아래 파일만 읽으므로, 폴더째 넣으면 CSV 로 실행되고 엑셀은 excel/ 안의 파일 하나를 넣어 시험한다.
// 기대 결과(규칙 수, 위반 건수)는 dq/reports/<kind>_<COHORT>/summary.json 에서 읽는다.
//
//   node app/build/pack-samples.cjs <출력 폴더> <버전>
//   → <출력 폴더>/SampleData-<버전>-<COHORT>-<kind>.zip ×12, SampleData-<버전>-all.zip

const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const { execFileSync } = require("node:child_process");
const { parse } = require("csv-parse/sync");
const XLSX = require("xlsx");
const YAML = require("yaml");

const ROOT = path.resolve(__dirname, "../..");
const [outDir, version] = process.argv.slice(2);
if (!outDir || !version) { console.error("사용법: node pack-samples.cjs <출력 폴더> <버전>"); process.exit(2); }

const profiles = YAML.parse(fs.readFileSync(path.join(ROOT, "spec/cohort_profiles.yaml"), "utf8")).cohorts;
const COHORTS = Object.keys(profiles);
const KINDS = ["clean", "dirty"];

function summary(kind, cohort) {
  const p = path.join(ROOT, "dq/reports", `${kind}_${cohort}`, "summary.json");
  if (!fs.existsSync(p)) return null;
  const s = JSON.parse(fs.readFileSync(p, "utf8"));
  return { rules: s.rules_total, violations: s.violations_total, run_date: s.run_date, failed: s.rules_failed };
}

function readme(kind, cohort, sum, manifestRows) {
  const kor = profiles[cohort].kor;
  const lines = [
    `K-AI 코호트 데이터 품질검증 견본 데이터 · ${kor} (${cohort}) · ${kind} · v${version}`,
    "",
    "이 폴더의 데이터는 명세에서 프로그램으로 만든 가상데이터입니다. 실제 환자나 병원과 무관합니다.",
    "Quality Validator 의 동작을 확인하는 용도이며, 폴더째 앱의 '검증 실행' 화면에 끌어다 놓으면 됩니다.",
    "",
    "파일",
    "  <TABLE>.csv            테이블별 CSV (UTF-8, 헤더 포함, 빈 값은 빈 문자열, 날짜 YYYY-MM-DD)",
    `  excel/${cohort}_${kind}.xlsx   같은 내용을 시트당 테이블 하나로 담은 엑셀 파일 (엑셀 입력 경로 시험용)`,
  ];
  if (kind === "dirty") lines.push("  fault_manifest.csv     주입한 오류의 정답표 (fault_id, 유형, 테이블, 행 키, 환자 ID, 원래 값, 바꾼 값, 잡아야 할 규칙 id)");
  lines.push("");
  if (kind === "clean") {
    lines.push("기대 결과", "  오류를 넣지 않은 데이터입니다. 모든 규칙을 통과해 위반 0건이 나와야 합니다.");
  } else {
    lines.push("기대 결과", `  오류 유형 30여 종을 ${manifestRows}건 주입했습니다. 규칙이 모두 잡아야 하며, 한 오류가 여러 규칙에 걸리므로 위반 건수는 주입 건수보다 많습니다.`);
  }
  if (sum) lines.push(`  검증 실행일 ${sum.run_date} 기준 참조 결과: 실행 규칙 ${sum.rules}개, 실패 규칙 ${sum.failed}개, 위반 ${sum.violations}건`);
  lines.push(
    "  검증 실행일을 다르게 두면 '미래 날짜' 규칙의 결과가 달라질 수 있습니다. 위 참조 결과와 맞추려면 실행 화면에서 검증 실행일을 위 날짜로 두세요.",
    "",
    "넣는 방법",
    "  CSV 로 시험: 이 폴더를 통째로 검증 실행 화면에 끌어다 놓습니다 (excel/ 하위 폴더는 무시됩니다).",
    "  엑셀로 시험: excel/ 안의 .xlsx 파일 하나만 넣습니다. 시트 이름이 테이블에 자동 대응됩니다.",
    "  두 방법의 결과는 같아야 합니다.",
    "",
    "저장소: https://github.com/nanumspace/KAI_DQ_App",
    "설명서: https://github.com/nanumspace/KAI_DQ_App/blob/main/manual/README.md",
    "라이선스: Apache-2.0",
    ""
  );
  return lines.join("\n");
}

function csvToSheet(file) {
  const rows = parse(fs.readFileSync(file, "utf8"), { bom: true, relax_column_count: true });
  const ws = XLSX.utils.aoa_to_sheet(rows.map((r) => r.map((v) => (v === "" ? null : v))));
  return ws;
}

fs.mkdirSync(outDir, { recursive: true });
const stage = fs.mkdtempSync(path.join(os.tmpdir(), "kai-samples-"));
const allDirs = [];
for (const cohort of COHORTS) for (const kind of KINDS) {
  const src = path.join(ROOT, "synth/output", kind, cohort);
  if (!fs.existsSync(src)) { console.warn(`건너뜀 (없음): ${src}`); continue; }
  const name = `SampleData-${version}-${cohort}-${kind}`;
  const dir = path.join(stage, name);
  fs.mkdirSync(dir, { recursive: true });
  const tables = profiles[cohort].tables;
  const wb = XLSX.utils.book_new();
  let manifestRows = 0;
  for (const f of fs.readdirSync(src).filter((f) => f.endsWith(".csv")).sort()) {
    fs.copyFileSync(path.join(src, f), path.join(dir, f));
    const table = f.replace(/\.csv$/, "");
    if (table === "fault_manifest") { manifestRows = parse(fs.readFileSync(path.join(src, f), "utf8"), { bom: true }).length - 1; continue; }
    if (!tables.includes(table)) continue;
    XLSX.utils.book_append_sheet(wb, csvToSheet(path.join(src, f)), table.slice(0, 31));
  }
  fs.mkdirSync(path.join(dir, "excel"));
  XLSX.writeFile(wb, path.join(dir, "excel", `${cohort}_${kind}.xlsx`), { compression: true });
  fs.writeFileSync(path.join(dir, "README.txt"), readme(kind, cohort, summary(kind, cohort), manifestRows));
  const zip = path.join(outDir, `${name}.zip`);
  fs.rmSync(zip, { force: true });
  execFileSync("zip", ["-r", "-q", "-X", zip, name], { cwd: stage });
  allDirs.push(name);
  console.log(`  ${path.basename(zip)}  ${(fs.statSync(zip).size / 1048576).toFixed(1)} MB`);
}
const allZip = path.join(outDir, `SampleData-${version}-all.zip`);
fs.rmSync(allZip, { force: true });
fs.writeFileSync(path.join(stage, "README.txt"), [
  `K-AI 코호트 데이터 품질검증 견본 데이터 전체 묶음 · v${version}`, "",
  "6개 코호트 × clean(오류 없음)/dirty(오류 주입) 12개 폴더입니다. 폴더마다 README.txt 에 파일 구성과 기대 결과가 있습니다.",
  "모두 가상데이터이며 실제 환자와 무관합니다. 폴더 하나를 앱의 '검증 실행' 화면에 끌어다 놓으면 됩니다.", "",
  "https://github.com/nanumspace/KAI_DQ_App", ""].join("\n"));
execFileSync("zip", ["-r", "-q", "-X", allZip, "README.txt", ...allDirs], { cwd: stage });
console.log(`  ${path.basename(allZip)}  ${(fs.statSync(allZip).size / 1048576).toFixed(1)} MB`);
fs.rmSync(stage, { recursive: true, force: true });
