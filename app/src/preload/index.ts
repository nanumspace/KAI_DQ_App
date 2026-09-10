// 렌더러에 노출하는 API (contextBridge). 렌더러는 window.api 만 쓴다.
import { contextBridge, ipcRenderer, webUtils } from "electron";
import type { Api } from "@shared/types";

function on<T>(channel: string, cb: (v: T) => void): () => void {
  const h = (_e: unknown, v: T) => cb(v);
  ipcRenderer.on(channel, h);
  return () => ipcRenderer.removeListener(channel, h);
}

const api: Api = {
  getConfig: () => ipcRenderer.invoke("config:get"),
  setConfig: (patch) => ipcRenderer.invoke("config:set", patch),
  listCohorts: () => ipcRenderer.invoke("cohorts:list"),
  listRules: () => ipcRenderer.invoke("rules:list"),
  chooseDirectory: (title) => ipcRenderer.invoke("dialog:directory", title),
  chooseFiles: () => ipcRenderer.invoke("dialog:files"),
  pathsForFiles: (files) => files.map((f) => webUtils.getPathForFile(f)).filter(Boolean),
  inspectInput: (cohort, paths, existing) => ipcRenderer.invoke("input:inspect", cohort, paths, existing),
  checkInput: (cohort, candidates, mapping) => ipcRenderer.invoke("input:check", cohort, candidates, mapping),
  previewSource: (c) => ipcRenderer.invoke("input:preview", c),
  exportTemplate: (cohort, kind) => ipcRenderer.invoke("template:export", cohort, kind),
  runValidation: (req) => ipcRenderer.invoke("run:start", req),
  onProgress: (cb) => on("run:progress", cb),
  listRuns: () => ipcRenderer.invoke("runs:list"),
  getRun: (runId) => ipcRenderer.invoke("runs:get", runId),
  getRunOutputs: (runId) => ipcRenderer.invoke("runs:outputs", runId),
  getFindings: (q) => ipcRenderer.invoke("findings:query", q),
  exportFile: (runId, key) => ipcRenderer.invoke("runs:exportFile", runId, key),
  exportBundle: (runId) => ipcRenderer.invoke("runs:exportBundle", runId),
  deleteRun: (runId) => ipcRenderer.invoke("runs:delete", runId),
  getDashboard: () => ipcRenderer.invoke("dashboard:get"),
  openPath: (p) => ipcRenderer.invoke("shell:open", p),
  onNav: (cb) => on("nav", cb),
  onSmokePlan: (cb) => on("smoke:plan", cb),
};

contextBridge.exposeInMainWorld("api", api);
