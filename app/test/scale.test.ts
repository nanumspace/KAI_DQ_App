// 규모 시험. 평소 시험에서는 돌지 않고 KAI_SCALE_DATA=<clean_v2 모양의 폴더> 를 주면 돈다.
//
//   KAI_SCALE_DATA=/path/to/scale npx vitest run test/scale.test.ts
//
// 병원 코호트는 수천 명이고 MEASUREMENT 는 수십만 행이다. 입력 처리(인식·사전 점검·정규화)와
// 엔진이 그 크기에서 얼마나 걸리고 메모리를 얼마나 쓰는지 잰다. 통과 조건은 느슨하다 —
// 죽지 않고 끝나며 위반이 0 이어야 한다. 시간은 로그로 남겨 설명서의 안내 문구에 쓴다.
import { describe, it, expect, beforeAll } from "vitest";
import fs from "node:fs";
import path from "node:path";
import os from "node:os";
import { setRoot, loadSpecV2, loadProfilesV2, runEngine } from "@engine/index.js";
import { inspectPaths, buildPlan, stageInputs } from "../src/main/input";

const ROOT = path.resolve(__dirname, "../..");
const DATA = process.env.KAI_SCALE_DATA ?? "";
const cohorts = DATA ? fs.readdirSync(DATA).filter((d) => fs.existsSync(path.join(DATA, d, "PERSON.csv"))) : [];

const mb = (n: number) => `${Math.round(n / 1048576)}MB`;
const sec = (ms: number) => `${(ms / 1000).toFixed(1)}s`;

describe.skipIf(!cohorts.length)("규모 시험", () => {
  let work: string;
  beforeAll(() => { setRoot(ROOT); work = fs.mkdtempSync(path.join(os.tmpdir(), "kai-scale-")); });

  for (const cohort of cohorts) {
    it(`${cohort}: 입력 처리와 엔진이 끝나고 위반 0`, async () => {
      const spec = loadSpecV2();
      const p = loadProfilesV2()[cohort];
      const tables = [...p.omop_tables, ...p.extension_tables];
      const src = path.join(DATA, cohort);
      const rows = Object.fromEntries(tables.filter((t) => fs.existsSync(path.join(src, `${t}.csv`)))
        .map((t) => [t, fs.readFileSync(path.join(src, `${t}.csv`), "utf-8").split("\n").length - 2]));
      const total = Object.values(rows).reduce((a, b) => a + b, 0);
      const bytes = tables.reduce((a, t) => a + (fs.existsSync(path.join(src, `${t}.csv`)) ? fs.statSync(path.join(src, `${t}.csv`)).size : 0), 0);

      const heap0 = process.memoryUsage().heapUsed;
      let t = performance.now();
      const candidates = inspectPaths([src]);
      const plan = buildPlan(cohort, tables, spec, candidates, undefined, ["PERSON"]);
      const tInspect = performance.now() - t;
      expect(plan.ok).toBe(true);

      t = performance.now();
      const staged = path.join(work, `${cohort}-staged`);
      stageInputs(plan.candidates, plan.mapping, staged, spec);
      const tStage = performance.now() - t;
      const heapStage = process.memoryUsage().heapUsed;

      t = performance.now();
      const stages: Record<string, number> = {};
      let last = performance.now(), lastStage = "";
      const s = await runEngine({
        cohort, today: "2026-09-07", spec: "v2", data: staged, out: path.join(work, `${cohort}-out`),
        onProgress: (pr) => { if (pr.stage !== lastStage) { const now = performance.now(); if (lastStage) stages[lastStage] = (stages[lastStage] ?? 0) + (now - last); last = now; lastStage = pr.stage; } },
      });
      const now = performance.now(); if (lastStage) stages[lastStage] = (stages[lastStage] ?? 0) + (now - last);
      const tEngine = now - t;
      const heapEnd = process.memoryUsage().heapUsed;
      const rss = process.memoryUsage().rss;

      const line = [
        `[scale] ${cohort}: 환자 ${rows["PERSON"]?.toLocaleString("ko-KR")}명 · 행 ${total.toLocaleString("ko-KR")} · ${mb(bytes)}`,
        `  인식·점검 ${sec(tInspect)} · 정규화 ${sec(tStage)} · 엔진 ${sec(tEngine)} (${Object.entries(stages).map(([k, v]) => `${k} ${sec(v)}`).join(", ")})`,
        `  힙 시작 ${mb(heap0)} → 정규화 후 ${mb(heapStage)} → 끝 ${mb(heapEnd)} · RSS ${mb(rss)}`,
        `  규칙 ${s.rules_total} · 위반 ${s.violations_total}`,
      ].join("\n");
      console.log(line);
      fs.appendFileSync(path.join(DATA, "_scale.log"), line + "\n", "utf-8");
      expect(s.violations_total).toBe(0);
    }, 1_800_000);
  }
});
