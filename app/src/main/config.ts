// 앱 설정 (userData/config.json)
import fs from "node:fs";
import path from "node:path";
import { app } from "electron";
import type { AppConfig } from "@shared/types";

function configPath(): string {
  return path.join(app.getPath("userData"), "config.json");
}

/** 명세·규칙 기본 위치: 개발 중에는 저장소 루트, 패키징 후에는 resources/kai */
export function defaultRoot(): string {
  if (app.isPackaged) return path.join(process.resourcesPath, "kai");
  return path.resolve(app.getAppPath(), "..");
}

export function readConfig(): AppConfig {
  let saved: Partial<AppConfig> = {};
  try { saved = JSON.parse(fs.readFileSync(configPath(), "utf-8")); } catch { /* 없으면 기본값 */ }
  return {
    root: saved.root && fs.existsSync(path.join(saved.root, "spec")) ? saved.root : defaultRoot(),
    defaultToday: saved.defaultToday ?? null,
    userData: app.getPath("userData"),
    packaged: app.isPackaged,
  };
}

export function writeConfig(patch: Partial<Pick<AppConfig, "root" | "defaultToday">>): AppConfig {
  const cur = readConfig();
  const next = { root: patch.root ?? cur.root, defaultToday: patch.defaultToday === undefined ? cur.defaultToday : patch.defaultToday };
  fs.mkdirSync(path.dirname(configPath()), { recursive: true });
  fs.writeFileSync(configPath(), JSON.stringify(next, null, 2), "utf-8");
  return readConfig();
}
