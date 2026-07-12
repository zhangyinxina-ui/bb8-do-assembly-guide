import assert from "node:assert/strict";
import { readdir, readFile, stat } from "node:fs/promises";
import { fileURLToPath } from "node:url";
import path from "node:path";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const output = path.join(root, "pages-dist");
const base = "/bb8-do-assembly-guide/";

async function files(directory) {
  const result = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const absolute = path.join(directory, entry.name);
    if (entry.isDirectory()) result.push(...await files(absolute));
    else result.push(absolute);
  }
  return result;
}

const index = await readFile(path.join(output, "index.html"), "utf8");
assert.match(index, new RegExp(`${base}assets/`));
assert.match(index, /REP·LAB \| BB-8 &(?:amp;)? D-O 1:1/);

const allFiles = await files(output);
assert.equal(allFiles.some((file) => file.endsWith(".blend")), false);
for (const required of [
  "model/BB8_three_view_dimension_sheet.png",
  "model/BB8_1to1_kinematic.glb",
  "downloads/DO_self_build_route.md",
  "downloads/do_self_build_bom.csv",
  "downloads/BB8_closed_loop_simulation.md",
  "downloads/closed_loop_telemetry.csv",
  "downloads/bb8_firmware_compile.json",
  ".nojekyll",
]) {
  assert.equal((await stat(path.join(output, required))).isFile(), true, required);
}

for (const file of allFiles.filter((name) => /\.(html|js|css|md|json|csv)$/i.test(name))) {
  const text = await readFile(file, "utf8");
  assert.doesNotMatch(text, /\/Users\/[^/\s]+|gho_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+/);
}

console.log(`PASS github_pages files=${allFiles.length} base=${base}`);
