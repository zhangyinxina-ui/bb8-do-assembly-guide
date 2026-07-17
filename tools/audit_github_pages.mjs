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
assert.match(index, /https:\/\/zhangyinxina-ui\.github\.io\/bb8-do-assembly-guide\/og\.png/);
const englishIndex = await readFile(path.join(output, "en", "index.html"), "utf8");
assert.match(englishIndex, new RegExp(`${base}assets/`));
assert.match(englishIndex, /BB-8 &(?:amp;)? D-O 1:1 Build Guide/);
assert.match(englishIndex, /https:\/\/zhangyinxina-ui\.github\.io\/bb8-do-assembly-guide\/og\.png/);

const allFiles = await files(output);
assert.equal(allFiles.some((file) => file.endsWith(".blend")), false);
for (const required of [
  "model/BB8_three_view_dimension_sheet.png",
  "model/BB8_1to1_kinematic.glb",
  "downloads/DO_self_build_route.md",
  "downloads/do_self_build_bom.csv",
  "downloads/do_mantis_video_audit.json",
  "downloads/do_safe_pin_variant_compile.json",
  "downloads/do_safe_pin_variant_wiring.csv",
  "downloads/build_do_safe_pin_variant.py",
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
  "downloads/BB8_阶段17_驱动电源器件选型门.md",
  "downloads/BB8_stage17_drive_power_component_selection_gate.md",
  "downloads/power_component_candidates.json",
  "downloads/power_component_selection_results.json",
  "downloads/verify_power_component_selection.py",
  "downloads/BB8_阶段18_模块化驱动电源舱布局门.md",
  "downloads/BB8_stage18_modular_drive_power_cassette_layout_gate.md",
  "downloads/stage18_layout_baseline.json",
  "downloads/stage18_power_cassette_layout.json",
  "downloads/stage18_power_cassette_results.json",
  "downloads/verify_power_cassette_layout.py",
  "downloads/BB8_阶段19_独立双许可PWM硬件门.md",
  "downloads/BB8_stage19_independent_dual_permissive_pwm_gate.md",
  "downloads/stage19_dual_permissive_gate_contract.json",
  "downloads/stage19_dual_permissive_gate_results.json",
  "downloads/stage19_blender_reopen_audit.json",
  "downloads/stage19_gate_truth_table.csv",
  "downloads/stage19_gate_bom.csv",
  "downloads/stage19_gate_netlist.csv",
  "downloads/verify_dual_permissive_gate.py",
  "downloads/stage19_gate_board_envelope.scad",
  "downloads/stage19_kicad_project.zip",
  "downloads/stage19_dual_permissive_gate.kicad_sch",
  "downloads/stage19_dual_permissive_gate.kicad_pro",
  "downloads/stage19_dual_permissive_gate.kicad_pcb",
  "downloads/stage19_symbols.kicad_sym",
  "downloads/BB8_stage19_dual_permissive_gate_schematic.pdf",
  "downloads/stage19_kicad_erc.json",
  "downloads/stage19_kicad_verification.json",
  "downloads/stage19_kicad_pcb_drc.json",
  "downloads/stage19_kicad_pcb_verification.json",
  "downloads/stage19_kicad_netlist.xml",
  "downloads/stage19_kicad_bom.csv",
  "downloads/generate_stage19_kicad.py",
  "downloads/generate_stage19_kicad_pcb.py",
  "downloads/verify_stage19_kicad.py",
  "downloads/verify_stage19_kicad_pcb.py",
  "downloads/export_stage19_kicad_pcb.py",
  "downloads/BB8_阶段20_结构载荷与公差门.md",
  "downloads/BB8_stage20_structural_load_and_tolerance_gate.md",
  "downloads/stage20_structural_load_contract.json",
  "downloads/stage20_structural_load_results.json",
  "downloads/stage20_structural_load_sweep.csv",
  "downloads/verify_stage20_structural_load_path.py",
  "downloads/BB8_阶段21_切向轮轴与预压滑台门.md",
  "downloads/BB8_stage21_tangent_wheel_preload_cassette_gate.md",
  "downloads/stage21_wheel_preload_contract.json",
  "downloads/stage21_wheel_preload_results.json",
  "downloads/stage21_wheel_preload_sweep.csv",
  "downloads/stage21_wheel_preload_bom.csv",
  "downloads/stage21_cad_manifest.json",
  "downloads/verify_stage21_wheel_preload.py",
  "downloads/build_stage21_wheel_preload_cad.py",
  "downloads/build_stage21_wheel_preload_cad.sh",
  "downloads/stage21_wheel_preload_adjuster.scad",
  "downloads/stage21_fixed_slider_plate.dxf",
  "downloads/stage21_moving_side_plate.dxf",
  "downloads/stage21_crowned_wheel_envelope.stl",
  "downloads/stage21_fixed_slider_plate_envelope.stl",
  "downloads/stage21_moving_side_plate_envelope.stl",
  "downloads/stage21_wheel_preload_assembly_envelope.stl",
  "images/BB8_stage21_wheel_preload_adjuster.png",
  "downloads/BB8_阶段22_标准同步带与轮轴底盘接口门.md",
  "downloads/BB8_stage22_catalog_belt_bearing_shaft_interface_gate.md",
  "downloads/stage22_drivetrain_interface_contract.json",
  "downloads/stage22_drivetrain_interface_results.json",
  "downloads/stage22_drivetrain_load_cases.csv",
  "downloads/stage22_drivetrain_interface_bom.csv",
  "downloads/stage22_cad_manifest.json",
  "downloads/verify_stage22_drivetrain_interface.py",
  "downloads/build_stage22_drivetrain_interface_cad.py",
  "downloads/build_stage22_drivetrain_interface_cad.sh",
  "downloads/stage22_drivetrain_interface.scad",
  "downloads/stage22_bearing_retainer.dxf",
  "downloads/stage22_rail_interface_bracket.dxf",
  "downloads/stage22_keyed_shaft_envelope.stl",
  "downloads/stage22_drivetrain_interface_assembly_envelope.stl",
  "images/BB8_stage22_drivetrain_interface.png",
  "og.png",
  "images/BB8_stage19_gate_pcb_top.svg",
  "images/BB8_stage19_gate_pcb_bottom.svg",
  "images/BB8_stage19_gate_pcb_top.png",
  "images/BB8_stage19_gate_pcb_bottom.png",
  "images/BB8_stage19_gate_pcb_isometric.png",
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
