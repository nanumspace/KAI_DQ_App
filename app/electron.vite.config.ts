import { defineConfig, externalizeDepsPlugin } from "electron-vite";
import react from "@vitejs/plugin-react";
import { resolve } from "node:path";

const engine = resolve(__dirname, "../dq-ts/src");
const shared = resolve(__dirname, "src/shared");

export default defineConfig({
  main: {
    plugins: [externalizeDepsPlugin()],
    resolve: { alias: { "@engine": engine, "@shared": shared } },
    build: {
      rollupOptions: {
        input: {
          index: resolve(__dirname, "src/main/index.ts"),
          worker: resolve(__dirname, "src/main/worker.ts"),
        },
      },
    },
  },
  preload: {
    plugins: [externalizeDepsPlugin()],
    resolve: { alias: { "@shared": shared } },
  },
  renderer: {
    plugins: [react()],
    resolve: { alias: { "@shared": shared } },
  },
});
