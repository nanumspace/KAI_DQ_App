// 앱 메인 프로세스 모듈의 시험 (Electron 없이 도는 부분만: 입력 처리)
import { defineConfig } from "vitest/config";
import { resolve } from "node:path";

export default defineConfig({
  resolve: { alias: { "@engine": resolve(__dirname, "../dq-ts/src"), "@shared": resolve(__dirname, "src/shared") } },
  test: { include: ["test/**/*.test.ts"], testTimeout: 120_000 },
});
