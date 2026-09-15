// 메인 프로세스: 창 · IPC · 입력 처리 · 엔진 워커 · 이력 DB · 출력물 · 스모크 모드
import fs from "node:fs";
import path from "node:path";
import { app, BrowserWindow, ipcMain, dialog, shell, utilityProcess } from "electron";
import { setRoot, loadSpec, loadProfiles, loadStructuralRules, loadSemanticRules,
         loadSpecV2, loadProfilesV2, loadStructuralRulesV2, loadSemanticRulesV2, readCsv, convertCrfDirectory, writeCrfTemplates, loadCrfSpec, formsForCohort } from "@engine/index.js";
import type { Summary, Spec } from "@engine/types.js";
import type { AppConfig, CohortInfo, RuleInfo, RunRequest, RunRecord, RunDetail, FindingsQuery, Dashboard, InputPlan, SourceCandidate, TemplateKind, OutputFile } from "@shared/types";
import { readConfig, writeConfig } from "./config";
import * as db from "./db";
import * as input from "./input";
import { writeExtraOutputs, runOutputs, exportBundle } from "./outputs";

const SMOKE = process.env.KAI_SMOKE === "1";
if (SMOKE) app.setPath("userData", path.join(process.env.KAI_SMOKE_OUT ?? app.getPath("temp"), "kai-smoke-userdata"));

let win: BrowserWindow | null = null;
let config: AppConfig;

function runsDir(): string { return path.join(app.getPath("userData"), "runs"); }

function createWindow(): BrowserWindow {
  const w = new BrowserWindow({
    width: 1480, height: 940, minWidth: 1100, minHeight: 700, show: false,
    title: "Quality Validator",
    backgroundColor: "#eef2f7",
    webPreferences: { preload: path.join(__dirname, "../preload/index.js"), sandbox: true, contextIsolation: true },
  });
  w.once("ready-to-show", () => w.show());
  if (process.env.ELECTRON_RENDERER_URL) w.loadURL(process.env.ELECTRON_RENDERER_URL);
  else w.loadFile(path.join(__dirname, "../renderer/index.html"));
  return w;
}

// ------------------------------------------------------------------ 명세·규칙
// 기본은 v2(저장 구조 재설계본)다. v1 로 낸 데이터를 아직 들고 있는 기관을 위해 옛 경로도 고를 수 있다.
function isV2(): boolean { return config.specVersion !== "v1"; }

function spec(): Spec { setRoot(config.root); return isV2() ? loadSpecV2() : loadSpec(); }

function cohorts(): CohortInfo[] {
  setRoot(config.root);
  if (isV2()) {
    return Object.entries(loadProfilesV2()).map(([id, p]) => ({ id, kor: p.kor, tables: [...p.omop_tables, ...p.extension_tables] }));
  }
  return Object.entries(loadProfiles()).map(([id, p]) => ({ id, kor: p.kor, tables: p.tables }));
}

function cohortOf(id: string): CohortInfo {
  const c = cohorts().find((x) => x.id === id);
  if (!c) throw new Error(`알 수 없는 코호트: ${id}`);
  return c;
}

function rules(): RuleInfo[] {
  setRoot(config.root);
  const v2 = isV2();
  const st: RuleInfo[] = (v2 ? loadStructuralRulesV2() : loadStructuralRules()).map((r) => ({
    id: r.id, name: r.name, category: r.category, subcategory: r.subcategory ?? "", severity: r.severity,
    table: r.table, fields: r.fields.join(","), check: r.check, desc: r.desc ?? "",
    scope: r.scope === "all" ? "all" : r.scope.join(","), kind: "structural",
  }));
  const se: RuleInfo[] = (v2 ? loadSemanticRulesV2() : loadSemanticRules()).map((r) => ({
    id: r.id, name: r.name, category: r.category, subcategory: r.subcategory ?? "", severity: r.severity,
    table: r.requires.join(","), fields: "", check: "sql", desc: r.desc ?? "",
    scope: r.scope === "all" ? "all" : r.scope.join(","), kind: "semantic", sql: r.sql,
  }));
  return [...st, ...se];
}

/** 견본 데이터 위치: 개발 중에는 synth/output, 설치본은 resources/kai/samples. 명세 판마다 폴더가 다르다. */
function sampleDir(cohort: string): string | null {
  const v2 = isV2();
  const cands = [
    path.join(config.root, v2 ? "samples_v2" : "samples", cohort),
    path.join(config.root, v2 ? "synth/output/clean_v2" : "synth/output/clean", cohort),
  ];
  return cands.find((p) => fs.existsSync(path.join(p, "PERSON.csv"))) ?? null;
}

// ------------------------------------------------------------------ 입력
/**
 * 없으면 검증 자체가 서지 않는 표.
 * v1 은 환자와 그 질환의 본표 둘이었다. v2 는 질환 본표가 없어지고 모두 OMOP 에 앉으므로 환자만 남는다.
 * 나머지가 없으면 막지 않고 경고만 낸다 — 엔진이 '테이블 없음'으로 따로 보고한다.
 */
function requiredTables(tables: string[]): string[] {
  if (isV2()) return ["PERSON"];
  const s = spec();
  const disease = tables.find((t) => s.tables[t].category === "disease");
  return disease ? ["PERSON", disease] : ["PERSON"];
}

function inspect(cohort: string, paths: string[], existing: SourceCandidate[] = []): InputPlan {
  const info = cohortOf(cohort);
  const fresh = input.inspectPaths(paths);
  const seen = new Set(fresh.map((c) => c.id));
  const candidates = [...existing.filter((c) => !seen.has(c.id)), ...fresh];
  return input.buildPlan(cohort, info.tables, spec(), candidates, undefined, requiredTables(info.tables));
}

function check(cohort: string, candidates: SourceCandidate[], mapping: Record<string, string>): InputPlan {
  return input.buildPlan(cohort, cohortOf(cohort).tables, spec(), candidates, mapping, requiredTables(cohortOf(cohort).tables));
}

async function exportTemplate(cohort: string, kind: TemplateKind): Promise<string | null> {
  const info = cohortOf(cohort); const s = spec();
  if (kind === "crf") {
    // v2: 병원이 채울 빈 서식. 고를 수 있는 코드 목록을 README 에 함께 적는다.
    const r = await dialog.showOpenDialog(win!, { title: "저장할 폴더 선택", properties: ["openDirectory", "createDirectory"] });
    if (r.canceled) return null;
    const dest = path.join(r.filePaths[0], `${cohort}_서식양식`);
    writeCrfTemplates(cohort, dest);
    return dest;
  }
  if (kind === "csv" || kind === "sample") {
    const r = await dialog.showOpenDialog(win!, { title: "저장할 폴더 선택", properties: ["openDirectory", "createDirectory"] });
    if (r.canceled) return null;
    const dest = path.join(r.filePaths[0], kind === "csv" ? `${cohort}_입력양식` : `${cohort}_견본데이터`);
    if (kind === "csv") input.writeCsvTemplates(info.tables, s, dest);
    else {
      const src = sampleDir(cohort);
      if (!src) throw new Error("견본 데이터가 없습니다");
      fs.mkdirSync(dest, { recursive: true });
      for (const t of info.tables) { const p = path.join(src, `${t}.csv`); if (fs.existsSync(p)) fs.copyFileSync(p, path.join(dest, `${t}.csv`)); }
    }
    return dest;
  }
  const name = kind === "xlsx" ? `${cohort}_입력양식.xlsx` : `${cohort}_컬럼명세서.xlsx`;
  const r = await dialog.showSaveDialog(win!, { defaultPath: name, filters: [{ name: "Excel", extensions: ["xlsx"] }] });
  if (r.canceled || !r.filePath) return null;
  if (kind === "xlsx") input.writeXlsxTemplate(info.tables, s, r.filePath); else input.writeSpecSheet(info.tables, s, r.filePath);
  return r.filePath;
}

// ------------------------------------------------------------------ 검증 실행
let running = false;

function runValidation(req: RunRequest): Promise<RunRecord> {
  if (running) return Promise.reject(new Error("이미 검증이 실행 중입니다"));
  const info = cohortOf(req.cohort);
  const plan = check(req.cohort, req.candidates, req.mapping);
  if (!plan.ok) return Promise.reject(new Error("사전 점검에서 오류가 있어 실행할 수 없습니다. 테이블 대응표를 확인하세요."));
  const now = new Date();
  const stamp = now.toISOString().replace(/[-:.]/g, "").replace("T", "_").slice(0, 18); // YYYYMMDD_HHMMSSmmm
  let runId = `${req.cohort}_${stamp}`;
  for (let k = 2; fs.existsSync(path.join(runsDir(), runId)); k++) runId = `${req.cohort}_${stamp}_${k}`;
  const outDir = path.join(runsDir(), runId);
  const inputDir = path.join(outDir, "input");
  const today = req.today || config.defaultToday || now.toISOString().slice(0, 10);
  const firstPath = req.candidates.find((c) => c.id === Object.values(req.mapping)[0])?.path ?? "";
  const label = req.label?.trim() || path.basename(path.dirname(firstPath) || firstPath) || req.cohort;
  running = true;
  const progress = (stage: string, done: number, total: number, text: string, pct: number) =>
    win?.webContents.send("run:progress", { runId, stage, done, total, text, pct });
  return new Promise<RunRecord>((resolve, reject) => {
    const finish = (fn: () => void) => { running = false; fn(); };
    try {
      progress("stage", 0, 1, "입력 파일을 UTF-8 CSV 로 정규화하는 중", 2);
      input.stageInputs(req.candidates, req.mapping, inputDir);
    } catch (e) { finish(() => reject(e)); return; }
    const child = utilityProcess.fork(path.join(__dirname, "worker.js"), [], { serviceName: "kai-dq-engine" });
    child.on("message", async (m: any) => {
      if (m.type === "progress") {
        const order = { load: 0, structural: 1, semantic: 2, write: 3 } as Record<string, number>;
        const base = [5, 12, 55, 95][order[m.stage] ?? 0]; const span = [7, 43, 40, 4][order[m.stage] ?? 0];
        progress(m.stage, m.done, m.total, m.text, Math.min(99, Math.round(base + (m.total ? (m.done / m.total) * span : 0))));
      } else if (m.type === "done") {
        try {
          const summary = m.summary as Summary;
          writeExtraOutputs(outDir, summary, { cohortKor: info.kor, label, runId });
          const findings = readCsv(path.join(outDir, "findings.csv"));
          const rec = await db.insertRun({ runId, cohort: req.cohort, cohortKor: info.kor, label, dataDir: firstPath ? path.dirname(firstPath) : inputDir, createdAt: now.toISOString(), summary, findings });
          progress("done", 1, 1, "완료", 100);
          finish(() => resolve(rec));
        } catch (e) { finish(() => reject(e)); }
        child.kill();
      } else if (m.type === "error") {
        finish(() => reject(new Error(m.message)));
        child.kill();
      }
    });
    child.on("exit", (code) => { if (running) finish(() => reject(new Error(`엔진 프로세스가 종료됨 (code ${code})`))); });
    child.postMessage({ type: "run", root: config.root, cohort: req.cohort, dataDir: inputDir, outDir, today, spec: config.specVersion });
  });
}

/** 폴더 하나로 자동 대응해 실행 (스모크 모드용) */
function runFromDir(cohort: string, dir: string, today: string, label: string): Promise<RunRecord> {
  const plan = inspect(cohort, [dir]);
  return runValidation({ cohort, candidates: plan.candidates, mapping: plan.mapping, today, label });
}

// ------------------------------------------------------------------ IPC
function registerIpc(): void {
  ipcMain.handle("config:get", () => config);
  ipcMain.handle("config:set", (_e, patch) => {
    // 명세 판을 바꾸면 코호트·규칙·양식이 전부 달라진다. 화면들이 이미 읽어 둔 것을 버리도록 다시 그린다.
    const changesSpec = patch?.specVersion && patch.specVersion !== config.specVersion;
    if (changesSpec && running) throw new Error("검증이 실행 중입니다. 끝난 뒤에 명세 판을 바꾸세요.");
    config = writeConfig(patch);
    if (changesSpec) setTimeout(() => win?.webContents.reload(), 400);
    return config;
  });
  ipcMain.handle("cohorts:list", () => cohorts());
  ipcMain.handle("rules:list", () => rules());
  ipcMain.handle("dialog:directory", async (_e, title?: string) => {
    const r = await dialog.showOpenDialog(win!, { title: title ?? "디렉터리 선택", properties: ["openDirectory"] });
    return r.canceled ? null : r.filePaths[0];
  });
  ipcMain.handle("dialog:directories", async (_e, title?: string) => {
    const r = await dialog.showOpenDialog(win!, { title: title ?? "폴더 선택", properties: ["openDirectory", "multiSelections"] });
    return r.canceled ? [] : r.filePaths;
  });
  ipcMain.handle("dialog:files", async () => {
    const r = await dialog.showOpenDialog(win!, { title: "CSV 또는 엑셀 파일 선택", properties: ["openFile", "multiSelections"],
      filters: [{ name: "CSV · 엑셀", extensions: ["csv", "tsv", "txt", "xlsx", "xlsm", "xls"] }] });
    return r.canceled ? [] : r.filePaths;
  });
  ipcMain.handle("input:inspect", (_e, cohort: string, paths: string[], existing?: SourceCandidate[]) => inspect(cohort, paths, existing));
  ipcMain.handle("input:check", (_e, cohort: string, candidates: SourceCandidate[], mapping: Record<string, string>) => check(cohort, candidates, mapping));
  ipcMain.handle("input:preview", (_e, c: SourceCandidate) => input.preview(c));
  ipcMain.handle("template:export", (_e, cohort: string, kind: TemplateKind) => exportTemplate(cohort, kind));
  // v2: 서식 CSV 가 든 폴더를 저장 레코드로 바꾼다. 결과 폴더를 그대로 검증에 넣을 수 있다.
  ipcMain.handle("crf:convert", (_e, req: { cohort: string; inDir: string; outDir?: string }) => {
    const outDir = req.outDir ?? path.join(app.getPath("userData"), "crf-staging", req.cohort);
    const r = convertCrfDirectory({ cohort: req.cohort, inDir: req.inDir, outDir });
    return { outDir, ...r };
  });
  ipcMain.handle("run:start", (_e, req: RunRequest) => runValidation(req));
  ipcMain.handle("runs:list", () => db.listRuns());
  ipcMain.handle("runs:get", async (_e, runId: string): Promise<RunDetail> => {
    const run = await db.getRun(runId);
    if (!run) throw new Error("실행 기록이 없습니다");
    const rp = path.join(runsDir(), runId, "report.md");
    return { run, rules: await db.getRuleResults(runId), report: fs.existsSync(rp) ? fs.readFileSync(rp, "utf-8") : "" };
  });
  ipcMain.handle("runs:outputs", (_e, runId: string) => runOutputs(path.join(runsDir(), runId)));
  ipcMain.handle("findings:query", (_e, q: FindingsQuery) => db.getFindings(q));
  ipcMain.handle("runs:exportFile", async (_e, runId: string, key: OutputFile["key"]) => {
    const f = runOutputs(path.join(runsDir(), runId)).files.find((x) => x.key === key);
    if (!f || !f.size) throw new Error("파일이 없습니다");
    const r = await dialog.showSaveDialog(win!, { defaultPath: `${runId}_${f.name}` });
    if (r.canceled || !r.filePath) return null;
    fs.copyFileSync(f.path, r.filePath);
    return r.filePath;
  });
  ipcMain.handle("runs:exportBundle", async (_e, runId: string) => {
    const r = await dialog.showOpenDialog(win!, { title: "결과를 저장할 폴더 선택", properties: ["openDirectory", "createDirectory"] });
    if (r.canceled) return null;
    return exportBundle(path.join(runsDir(), runId), runId, r.filePaths[0]);
  });
  ipcMain.handle("runs:delete", async (_e, runId: string) => {
    await db.deleteRun(runId);
    fs.rmSync(path.join(runsDir(), runId), { recursive: true, force: true });
  });
  ipcMain.handle("dashboard:get", async (): Promise<Dashboard> => {
    const rs = rules();
    const structural = rs.filter((r) => r.kind === "structural").length;
    return db.dashboard({ structural, semantic: rs.length - structural, total: rs.length });
  });
  ipcMain.handle("shell:open", (_e, p: string) => shell.openPath(p));
}

// ------------------------------------------------------------------ 스모크 모드
// KAI_SMOKE=1: 가상데이터로 검증을 자동 실행하고 각 화면을 PNG 로 찍은 뒤 종료한다 (자동 점검용).
async function smoke(): Promise<void> {
  const out = process.env.KAI_SMOKE_OUT ?? app.getPath("temp");
  fs.mkdirSync(out, { recursive: true });
  const log = (s: string) => { console.log(`[smoke] ${s}`); fs.appendFileSync(path.join(out, "smoke.log"), s + "\n"); };
  const wait = (ms: number) => new Promise((r) => setTimeout(r, ms));
  try {
    // 켜져 있는 명세 판의 가상데이터를 쓴다 (v2 는 clean_v2 / dirty_v2)
    const sfx = isV2() ? "_v2" : "";
    const synth = path.join(config.root, "synth/output");
    log(`명세 ${config.specVersion} · 규칙 ${rules().length}개`);
    // 엑셀 입력 경로 시험: 폐암 dirty 를 엑셀 한 파일(시트당 테이블)로 만들어 넣는다
    const xlsxPath = path.join(out, "LUNG_CANCER_dirty.xlsx");
    {
      const XLSX = await import("xlsx");
      const wb = XLSX.utils.book_new();
      for (const t of cohortOf("LUNG_CANCER").tables) {
        const p = path.join(synth, `dirty${sfx}/LUNG_CANCER`, `${t}.csv`);
        if (!fs.existsSync(p)) continue;
        const raw = readCsv(p);
        const rows = [raw.columns, ...Array.from({ length: raw.n }, (_, i) => raw.columns.map((c) => raw.cols.get(c)![i]))];
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rows), t.slice(0, 31));
      }
      XLSX.writeFile(wb, xlsxPath);
    }
    for (const [cohort, dir, label] of [["LUNG_CANCER", path.join(synth, `clean${sfx}/LUNG_CANCER`), "clean 가상데이터"], ["DIABETES", path.join(synth, `dirty${sfx}/DIABETES`), "dirty 가상데이터"]] as const) {
      const rec = await runFromDir(cohort, dir, "2026-09-07", label);
      log(`run ${rec.run_id}: rules=${rec.rules_total} violations=${rec.violations_total}`);
    }
    const planX = inspect("LUNG_CANCER", [xlsxPath]);
    log(`xlsx plan: candidates=${planX.candidates.length} mapped=${Object.keys(planX.mapping).length} errors=${planX.errors} warnings=${planX.warnings}`);
    const recX = await runValidation({ cohort: "LUNG_CANCER", candidates: planX.candidates, mapping: planX.mapping, today: "2026-09-07", label: "dirty 엑셀 입력" });
    log(`run ${recX.run_id}: rules=${recX.rules_total} violations=${recX.violations_total} (엑셀)`);
    let planFolders: InputPlan | null = null;
    // 폴더 두 곳을 한 번에 넣는 길: v2 는 서식을 바꾼 폴더와 EHR 추출본 폴더가 따로 온다.
    {
      const src = path.join(synth, `clean${sfx}/LUNG_CANCER`);
      const tables = cohortOf("LUNG_CANCER").tables.filter((t) => fs.existsSync(path.join(src, `${t}.csv`)));
      const half = Math.ceil(tables.length / 2);
      const dirs = [path.join(out, "split/EHR추출본"), path.join(out, "split/서식변환결과")];
      dirs.forEach((d) => fs.mkdirSync(d, { recursive: true }));
      tables.forEach((t, i) => fs.copyFileSync(path.join(src, `${t}.csv`), path.join(dirs[i < half ? 0 : 1], `${t}.csv`)));
      const plan2 = inspect("LUNG_CANCER", dirs);
      planFolders = plan2;
      log(`폴더 2곳: 후보 ${plan2.candidates.length}개, 대응 ${Object.keys(plan2.mapping).length}/${tables.length}, 오류 ${plan2.errors} 주의 ${plan2.warnings}`);
      const rec2 = await runValidation({ cohort: "LUNG_CANCER", candidates: plan2.candidates, mapping: plan2.mapping, today: "2026-09-07", label: "폴더 2곳 입력" });
      log(`run ${rec2.run_id}: rules=${rec2.rules_total} violations=${rec2.violations_total} (폴더 2곳)`);
      // 상위 폴더 하나만 넣어도 아래 두 폴더를 찾아야 한다
      const planP = inspect("LUNG_CANCER", [path.join(out, "split")]);
      log(`상위 폴더 1곳: 후보 ${planP.candidates.length}개, 대응 ${Object.keys(planP.mapping).length}/${tables.length}`);
      // 같은 이름이 두 폴더에 있으면 어느 것을 쓰는지 말해야 한다
      fs.copyFileSync(path.join(src, "PERSON.csv"), path.join(dirs[1], "PERSON.csv"));
      const planD = inspect("LUNG_CANCER", dirs);
      const dup = planD.tables.find((t) => t.table === "PERSON")?.issues.filter((i) => i.text.includes("같은 이름")) ?? [];
      log(`이름 겹침: 후보 ${planD.candidates.length}개, PERSON 안내 ${dup.length}건 — ${dup[0]?.text ?? "(없음)"}`);
      fs.rmSync(path.join(dirs[1], "PERSON.csv"));
    }
    let crfPayload: unknown = null;
    // v2 서식 경로: 빈 양식을 만들고, 채워진 서식을 레코드로 되돌린다
    {
      const blank = path.join(out, "crf-blank");
      const files = writeCrfTemplates("LUNG_CANCER", blank);
      log(`crf 빈 양식 ${files.length}개 → ${blank}`);
      // 병원이 채운 서식 대신, 가상데이터의 확장 저장을 서식 모양으로 되돌려 쓴다
      const crfIn = path.join(out, "crf-in");
      fs.mkdirSync(crfIn, { recursive: true });
      const toCode = new Map<string, string>();
      for (const line of fs.readFileSync(path.join(config.root, "spec/v2/vocab/CONCEPT_SET_ITEM.csv"), "utf-8").split(/\r?\n/).slice(1)) {
        const [, conceptId, code] = line.split(",");
        if (conceptId) toCode.set(conceptId, code ?? "");
      }
      const crfSpec = loadCrfSpec();
      for (const form of formsForCohort(crfSpec, "LUNG_CANCER")) {
        if (form.mapping) continue;                       // 투영 서식은 되돌릴 수 없다
        const src = path.join(synth, "clean_v2/LUNG_CANCER", `${form.name}.csv`);
        if (!fs.existsSync(src)) continue;
        const df = readCsv(src);
        const names = form.fields.map((f) => f.name);
        const lines = [names.join(",")];
        for (let i = 0; i < Math.min(df.n, 20); i++) {
          lines.push(form.fields.map((f) => {
            const col = f.target?.column;
            const v = col && df.cols.has(col) ? df.cols.get(col)![i] : "";
            const out = col?.endsWith("_concept_id") && f.codelist ? (toCode.get(v) ?? v) : v;
            return /[",\n]/.test(out) ? `"${out.replace(/"/g, '""')}"` : out;
          }).join(","));
        }
        fs.writeFileSync(path.join(crfIn, `${form.name}.csv`), lines.join("\n") + "\n", "utf-8");
      }
      const crfOut = path.join(out, "crf-out");
      const rc = convertCrfDirectory({ cohort: "LUNG_CANCER", inDir: crfIn, outDir: crfOut });
      const rows = Object.values(rc.formsRead).reduce((a, b) => a + b, 0);
      const recs = Object.values(rc.tablesWritten).reduce((a, b) => a + b, 0);
      log(`crf 변환: 서식 ${Object.keys(rc.formsRead).length}개 ${rows}행 → 레코드 ${recs}건, 확인할 점 ${rc.issues.length}건, EHR 표 ${rc.tablesFromEhr.length}개`);
      crfPayload = { inDir: crfIn, result: { outDir: crfOut, ...rc } };
    }
    // 화면 캡처: 검증 실행 화면은 대응표 상태를 보기 위해 렌더러에 계획을 넣어 준다
    // 화면은 폴더 2곳을 넣은 모습으로 찍는다 (엑셀 경로는 위에서 실행으로 확인했다)
    win!.webContents.send("smoke:plan", planFolders ?? planX);
    for (const page of ["run", "crf", "report", "findings", "dashboard", "rules", "monitor", "settings"]) {
      win!.webContents.send("nav", page);
      // 화면이 붙은 뒤에 보내야 한다 — 그 화면은 열릴 때 비로소 듣기 시작한다
      await wait(400);
      if (page === "crf" && crfPayload) win!.webContents.send("smoke:crf", crfPayload);
      await wait(page === "dashboard" || page === "run" ? 2100 : 1100);
      const img = await win!.webContents.capturePage();
      fs.writeFileSync(path.join(out, `${page}.png`), img.toPNG());
      log(`captured ${page}`);
    }
    log("ok");
  } catch (e) {
    log(`error ${(e as Error).stack ?? e}`);
  } finally {
    app.quit();
  }
}

// ------------------------------------------------------------------ 시작
app.whenReady().then(async () => {
  config = readConfig();
  // 자동 점검에서는 어느 명세 판으로 돌릴지 환경변수로 고른다 (v1 회귀 확인용)
  if (SMOKE && (process.env.KAI_SMOKE_SPEC === "v1" || process.env.KAI_SMOKE_SPEC === "v2")) {
    config = writeConfig({ specVersion: process.env.KAI_SMOKE_SPEC });
  }
  await db.openDb(path.join(app.getPath("userData"), "history.duckdb"));
  registerIpc();
  win = createWindow();
  win.on("closed", () => { win = null; });
  if (SMOKE) win.webContents.once("did-finish-load", () => { setTimeout(() => void smoke(), 800); });
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) win = createWindow(); });
});

app.on("window-all-closed", () => { db.closeDb(); if (process.platform !== "darwin" || SMOKE) app.quit(); });
app.on("before-quit", () => db.closeDb());
