import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";
import { resolve } from "path";

export default defineConfig({
  server: {
    watch: {
      ignored: ["**/node_modules/**", "Immunoinformatics/**"],
    },
    port: 1234,
    proxy: {
      "/immuno": {
        target: "http://127.0.0.1:3123/plugins/pages/immuno.immuno/",
        changeOrigin: true,
      },
      "/results_api": {
        target: "http://127.0.0.1:3123/plugins/pages/immuno.results/",
        changeOrigin: true,
      },
    },
    open: "results.html",
  },
  build: {
    outDir: "Immunoinformatics/Pages",
    emptyOutDir: false,
    rollupOptions: {
      input: {
        index: resolve(__dirname, "index.html"),
        results: resolve(__dirname, "results.html"),
      },
    },
  },
  base: "./",
  plugins: [react(), tsconfigPaths()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.mjs",
  },
});
