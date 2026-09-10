// 메인 프로세스: 창 · IPC · 입력 처리 · 엔진 워커 · 이력 DB · 출력물 · 스모크 모드
import fs from "node:fs";
import path from "node:path";
import { app, BrowserWindow, ipcMain, dialog, shell, utilityProcess } from "electron";
import { setRoot, loadSpec, loadProfiles, loadStructuralRules, loadSemanticRules, readCsv } from "@engine/index.js";
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
function spec(): Spec { setRoot(config.root); return loadSpec(); }

function cohorts(): CohortInfo[] {
  setRoot(config.root);
  return Object.entries(loadProfiles()).map(([id, p]) => ({ id, kor: p.kor, tables: p.tables }));
}

function cohortOf(id: string): CohortInfo {
  const c = cohorts().find((x) => x.id === id);
  if (!c) throw new Error(`알 수 없는 코호트: ${id}`);
  return c;
}

function rules(): RuleInfo[] {
  setRoot(config.root);
  const st: RuleInfo[] = loadStructuralRules().map((r) => ({
    id: r.id, name: r.name, category: r.category, subcategory: r.subcategory ?? "", severity: r.severity,
    table: r.table, fields: r.fields.join(","), check: r.check, desc: r.desc ?? "",
    scope: r.scope === "all" ? "all" : r.scope.join(","), kind: "structural",
  }));
  const se: RuleInfo[] = loadSemanticRules().map((r) => ({
    id: r.id, name: r.name, category: r.category, subcategory: r.subcategory ?? "", severity: r.severity,
    table: r.requires.join(","), fields: "", check: "sql", desc: r.desc ?? "",
    scope: r.scope === "all" ? "all" : r.scope.join(","), kind: "semantic", sql: r.sql,
  }));
  return [...st, ...se];
}

/** 견본 데이터 위치: 개발 중에는 synth/output/clean, 설치본은 resources/kai/samples */
function sampleDir(cohort: string): string | null {
  const cands = [path.join(config.root, "samples", cohort), path.join(config.root, "synth/output/clean", cohort)];
  return cands.find((p) => fs.existsSync(path.join(p, "PERSON.csv"))) ?? null;
}

// ------------------------------------------------------------------ 입력
function inspect(cohort: string, paths: string[], existing: SourceCandidate[] = []): InputPlan {
  const info = cohortOf(cohort);
  const fresh = input.inspectPaths(paths);
  const seen = new Set(fresh.map((c) => c.id));
  const candidates = [...existing.filter((c) => !seen.has(c.id)), ...fresh];
  return input.buildPlan(cohort, info.tables, spec(), candidates);
}

function check(cohort: string, candidates: SourceCandidate[], mapping: Record<string, string>): InputPlan {
  return input.buildPlan(cohort, cohortOf(cohort).tables, spec(), candidates, mapping);
}

async function exportTemplate(cohort: string, kind: TemplateKind): Promise<string | null> {
  const info = cohortOf(cohort); const s = spec();
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
    child.postMessage({ type: "run", root: config.root, cohort: req.cohort, dataDir: inputDir, outDir, today });
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
  ipcMain.handle("config:set", (_e, patch) => { config = writeConfig(patch); return config; });
  ipcMain.handle("cohorts:list", () => cohorts());
  ipcMain.handle("rules:list", () => rules());
  ipcMain.handle("dialog:directory", async (_e, title?: string) => {
    const r = await dialog.showOpenDialog(win!, { title: title ?? "디렉터리 선택", properties: ["openDirectory"] });
    return r.canceled ? null : r.filePaths[0];
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
    const synth = path.join(config.root, "synth/output");
    // 엑셀 입력 경로 시험: 폐암 dirty 를 엑셀 한 파일(시트당 테이블)로 만들어 넣는다
    const xlsxPath = path.join(out, "LUNG_CANCER_dirty.xlsx");
    {
      const XLSX = await import("xlsx");
      const wb = XLSX.utils.book_new();
      for (const t of cohortOf("LUNG_CANCER").tables) {
        const p = path.join(synth, "dirty/LUNG_CANCER", `${t}.csv`);
        if (!fs.existsSync(p)) continue;
        const raw = readCsv(p);
        const rows = [raw.columns, ...Array.from({ length: raw.n }, (_, i) => raw.columns.map((c) => raw.cols.get(c)![i]))];
        XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet(rows), t.slice(0, 31));
      }
      XLSX.writeFile(wb, xlsxPath);
    }
    for (const [cohort, dir, label] of [["LUNG_CANCER", path.join(synth, "clean/LUNG_CANCER"), "clean 가상데이터"], ["DIABETES", path.join(synth, "dirty/DIABETES"), "dirty 가상데이터"]] as const) {
      const rec = await runFromDir(cohort, dir, "2026-09-07", label);
      log(`run ${rec.run_id}: rules=${rec.rules_total} violations=${rec.violations_total}`);
    }
    const planX = inspect("LUNG_CANCER", [xlsxPath]);
    log(`xlsx plan: candidates=${planX.candidates.length} mapped=${Object.keys(planX.mapping).length} errors=${planX.errors} warnings=${planX.warnings}`);
    const recX = await runValidation({ cohort: "LUNG_CANCER", candidates: planX.candidates, mapping: planX.mapping, today: "2026-09-07", label: "dirty 엑셀 입력" });
    log(`run ${recX.run_id}: rules=${recX.rules_total} violations=${recX.violations_total} (엑셀)`);
    // 화면 캡처: 검증 실행 화면은 대응표 상태를 보기 위해 렌더러에 계획을 넣어 준다
    win!.webContents.send("smoke:plan", planX);
    for (const page of ["run", "report", "findings", "dashboard", "rules", "monitor", "settings"]) {
      win!.webContents.send("nav", page);
      await wait(page === "dashboard" || page === "run" ? 2500 : 1500);
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
  await db.openDb(path.join(app.getPath("userData"), "history.duckdb"));
  registerIpc();
  win = createWindow();
  win.on("closed", () => { win = null; });
  if (SMOKE) win.webContents.once("did-finish-load", () => { setTimeout(() => void smoke(), 800); });
  app.on("activate", () => { if (BrowserWindow.getAllWindows().length === 0) win = createWindow(); });
});

app.on("window-all-closed", () => { db.closeDb(); if (process.platform !== "darwin" || SMOKE) app.quit(); });
app.on("before-quit", () => db.closeDb());
