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
const englishIndex = await readFile(path.join(output, "en", "index.html"), "utf8");
assert.match(englishIndex, new RegExp(`${base}assets/`));
assert.match(englishIndex, /BB-8 &(?:amp;)? D-O 1:1 Build Guide/);

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
  "downloads/BB8_stage11_sensor_adapter.md",
  "downloads/sensor_adapter_contract.json",
  "downloads/BB8_stage12_power_safety.md",
  "downloads/BB8_stage13_power_hardware.md",
  "downloads/BB8_阶段14_质量质心与惯量验证.md",
  "downloads/BB8_stage14_mass_cg_inertia_validation.md",
  "downloads/mass_properties_input.json",
  "downloads/mass_properties_results.json",
  "downloads/mass_properties_scenarios.csv",
  "downloads/BB8_阶段15_驱动电源与动态稳定性.md",
  "downloads/BB8_stage15_drive_power_dynamic_stability.md",
  "downloads/stability_envelope_input.json",
  "downloads/stability_envelope_results.json",
  "downloads/stability_envelope_sweep.csv",
  "downloads/BB8_阶段16_真机调试证据门.md",
  "downloads/BB8_stage16_physical_commissioning_evidence_gate.md",
  "downloads/commissioning_test_plan.json",
  "downloads/commissioning_evidence.json",
  "downloads/commissioning_results.json",
  "downloads/parse_bb8_telemetry.py",
  "downloads/verify_commissioning_evidence.py",
  "downloads/power_safety_contract.json",
  "downloads/power_safety_replay.csv",
  ".nojekyll",
]) {
  assert.equal((await stat(path.join(output, required))).isFile(), true, required);
}

for (const file of allFiles.filter((name) => /\.(html|js|css|md|json|csv)$/i.test(name))) {
  const text = await readFile(file, "utf8");
  assert.doesNotMatch(text, /\/Users\/[^/\s]+|gho_[A-Za-z0-9_]+|github_pat_[A-Za-z0-9_]+/);
}

console.log(`PASS github_pages files=${allFiles.length} base=${base}`);
