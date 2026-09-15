/**
 * Remove what `vite build` writes into Immunoinformatics/Pages.
 *
 * The build runs with `emptyOutDir: false`, because Pages is a folder of the
 * plugin and not a plain output directory, so nothing clears the previous
 * build on its own: every run leaves the assets of the last one behind under
 * their old hashed names, and they end up in the .hp. Hence this script, which
 * build_plugin.sh runs before building.
 *
 * Only the generated files are removed. Anything else that lives in Pages (the
 * documentation PDFs, which .gitignore keeps tracked) is left alone; the
 * examples copied from public/ are rewritten by the build that follows.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));

// `build.outDir` and the entries of `build.rollupOptions.input` in
// vite.config.mjs: keep the two lists in step
const outDir = path.join(root, "Immunoinformatics", "Pages");
const pages = ["index.html", "results.html", "tcoarse.html"];

const targets = [path.join(outDir, "assets"), ...pages.map((p) => path.join(outDir, p))];

for (const target of targets) {
  if (!fs.existsSync(target)) {
    continue;
  }

  fs.rmSync(target, { recursive: true, force: true });

  console.log(`Removed ${path.relative(root, target)}`);
}
