import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tsconfigPaths from "vite-tsconfig-paths";

export default defineConfig({
  server: {
    port: 1234,
    proxy: {
      "/immuno": {
        target: "http://127.0.0.1:3000/plugins/pages/immuno.immuno/",
        changeOrigin: true,
      },
      "/api": {
        target: "http://127.0.0.1:3000/",
        changeOrigin: true,
      },
    },
  },
  build: {
    outDir: "Immunoinformatics/Pages",
    emptyOutDir: false,
  },
  base: "./",
  plugins: [react(), tsconfigPaths()],
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: "./vitest.setup.mjs",
  },
});
