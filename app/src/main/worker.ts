// 검증 엔진 워커 (Electron utilityProcess). 메인 프로세스와 분리되어 화면이 멈추지 않는다.
// 메시지: {type:"run", root, cohort, dataDir, outDir, today} → progress ... → {type:"done", summary} | {type:"error", message}
import { runEngine, setRoot } from "@engine/index.js";

interface RunMsg { type: "run"; root: string; cohort: string; dataDir: string; outDir: string; today?: string }

const port = process.parentPort;

port.on("message", async (e: Electron.MessageEvent) => {
  const m = e.data as RunMsg;
  if (!m || m.type !== "run") return;
  setRoot(m.root);
  try {
    const summary = await runEngine({
      cohort: m.cohort, data: m.dataDir, out: m.outDir, today: m.today,
      onProgress: (p) => port.postMessage({ type: "progress", ...p }),
    });
    port.postMessage({ type: "done", summary });
  } catch (err) {
    const e2 = err as Error;
    port.postMessage({ type: "error", message: e2?.stack ?? String(err) });
  }
});
