import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const developmentPreviewMeta =
  /<meta(?=[^>]*\bname=["']codex-preview["'])(?=[^>]*\bcontent=["']development["'])[^>]*>/i;

async function render(pathname = "/") {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request(`http://localhost${pathname}`, {
      headers: { accept: "text/html" },
    }),
    {
      ASSETS: {
        fetch: async () => new Response("Not found", { status: 404 }),
      },
    },
    {
      waitUntil() {},
      passThroughOnException() {},
    },
  );
}

test("server-renders the BB-8 and D-O build guide", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);

  const html = await response.text();
  assert.doesNotMatch(html, developmentPreviewMeta);
  assert.match(html, /BB-8 &amp; D-O 1:1/);
  assert.match(html, /GitHub 项目/);
  assert.match(html, /https:\/\/github\.com\/zhangyinxina-ui\/bb8-do-assembly-guide/);
  assert.match(html, /508/);
  assert.match(html, /Printed Droid/);
  assert.doesNotMatch(html, /href=["']\/model\/BB8_1to1_screen_referenced\.blend/);
  assert.match(html, /BB8_internal_three_view\.png/);
  assert.match(html, /internal_assembly_manifest\.csv/);
  assert.match(html, /386个总对象、182个内部对象/);
  assert.match(html, /150个制造对象、9个非制造工程标记和23个阶段19非制造预CAD参考对象/);
  assert.match(html, /BB8_motor_selection\.md/);
  assert.match(html, /IG42E-24K/);
  assert.match(html, /PCD 35 mm/);
  assert.match(html, /310 mm轮距/);
  assert.match(html, /494 mm密封圈/);
  assert.match(html, /12段动力\/编码器线束/);
  assert.match(html, /6\+6磁体包络/);
  assert.match(html, /装机拉力验收线为40 N/);
  assert.match(html, /BB8_magnetic_coupling\.md/);
  assert.match(html, /downloads\/BB8_BOM\.md/);
  assert.match(html, /downloads\/DO_resources\.md/);
  assert.match(html, /个人非商业许可/);
  assert.match(html, /v3\.4\.3 固定到 e90aacd/);
  assert.match(html, /Mega 2560 真编译通过：Flash 17%，RAM 18%/);
  assert.match(html, /机械 CAD\/STL 为0/);
  assert.match(html, /60 mm无轮调试支架/);
  assert.match(html, /Denton V1 页面标 CC BY 4\.0/);
  assert.match(html, /头部缺失、STEP 待后续/);
  assert.match(html, /JRIZZ \/ Cults 页面列出 Fusion 360 F3Z、STL、机器人端与遥控端 Arduino 草图/);
  assert.match(html, /购买和接受 CULTS Private Use 必须等待用户明确确认/);
  assert.match(html, /WF3D 约300 mm、32文件模型为 CC BY-NC-SA 4\.0 静态展示件/);
  assert.match(html, /Gambody有116个STL和518 mm关节版/);
  assert.match(html, /https:\/\/www\.thingiverse\.com\/thing:4189546/);
  assert.match(html, /https:\/\/cults3d\.com\/en\/3d-model\/gadget\/d-o-droid-star-wars-droid/);
  assert.match(html, /https:\/\/www\.printables\.com\/model\/147063-star-wars-d-o-droid/);
  assert.match(html, /DO_resource_audit\.md/);
  assert.match(html, /do_resource_manifest\.json/);
  assert.match(html, /do_mantis_video_audit\.json/);
  assert.match(html, /DO_self_build_route\.md/);
  assert.match(html, /do_self_build_bom\.csv/);
  assert.match(html, /D01–D16调试门/);
  assert.match(html, /现有26项采购状态表/);
  assert.match(html, /MDD10A与两块MD10C的来源冲突/);
  assert.match(html, /D0\/D1舵机与Serial0引脚争用/);
  assert.match(html, /官网v2.1的D2–D5接线表与v3.4.3源码不一致/);
  assert.match(html, /官网12个附件已在本机逐项校验哈希/);
  assert.match(html, /AIO32附件22个源码文件已用ESP32 core 3\.3\.7实编译通过/);
  assert.match(html, /Flash 41%、RAM 15%/);
  assert.match(html, /手册遗漏SensorLib依赖/);
  assert.match(html, /do_aio32_firmware_compile\.json/);
  assert.match(html, /泛名v3.4 ZIP实际仍是v3.4.0/);
  assert.match(html, /下载26项采购门控BOM/);
  assert.match(html, /BB8_kinematic_cycle\.mp4/);
  assert.match(html, /BB8_1to1_kinematic\.glb/);
  assert.match(html, /BB8_internal_mechanism_mm\.stl/);
  assert.match(html, /1\.595929/);
  assert.match(html, /BB8_controller_core\.zip/);
  assert.match(html, /BB8_ESP32_S3_firmware\.zip/);
  assert.match(html, /双正交编码器、MPU6050 和双 INA226 适配均已通过 ESP32-S3 编译/);
  assert.match(html, /BB8_physics_validation\.md/);
  assert.match(html, /8\.463 kg 名义质量/);
  assert.match(html, /质心下置 56\.2 mm/);
  assert.match(html, /3°动态坡道点/);
  assert.match(html, /BB8_multibody_validation\.md/);
  assert.match(html, /2\.07× 连续扭矩裕量/);
  assert.match(html, /4\.22°合成倾角/);
  assert.match(html, /断电坡道不驻车/);
  assert.match(html, /110 mm旧假设/);
  assert.match(html, /differential_turn\.csv/);
  assert.match(html, /11 类故障锁存/);
  assert.match(html, /BB8_closed_loop_simulation\.md/);
  assert.match(html, /closed_loop_telemetry\.csv/);
  assert.match(html, /bb8_firmware_compile\.json/);
  assert.match(html, /0\.00772 m\/s/);
  assert.match(html, /91\.20° 动态转弯/);
  assert.match(html, /BB8_stage11_sensor_adapter\.md/);
  assert.match(html, /sensor_adapter_contract\.json/);
  assert.match(html, /编码器 CPR 默认为0/);
  assert.match(html, /BB8_stage12_power_safety\.md/);
  assert.match(html, /power_safety_contract\.json/);
  assert.match(html, /power_safety_replay\.csv/);
  assert.match(html, /硬件急停去能/);
  assert.match(html, /双2 mΩ四线分流器/);
  assert.match(html, /BB8_stage13_power_hardware\.md/);
  assert.match(html, /BB8_阶段14_质量质心与惯量验证\.md/);
  assert.match(html, /BB8_stage14_mass_cg_inertia_validation\.md/);
  assert.match(html, /mass_properties_results\.json/);
  assert.match(html, /BB8_阶段15_驱动电源与动态稳定性\.md/);
  assert.match(html, /stability_envelope_results\.json/);
  assert.match(html, /双通道常闭急停/);
  assert.match(html, /真实带电试验仍为NOT_RUN/);
  assert.match(html, /19项真机调试门/);
  assert.match(html, /当前0 \/ 19/);
  assert.match(html, /HOLD_PHYSICAL_TESTS_NOT_RUN/);
  assert.match(html, /BB8_阶段16_真机调试证据门\.md/);
  assert.match(html, /commissioning_test_plan\.json/);
  assert.match(html, /commissioning_evidence\.json/);
  assert.match(html, /commissioning_results\.json/);
  assert.match(html, /parse_bb8_telemetry\.py/);
  assert.match(html, /verify_commissioning_evidence\.py/);
  assert.match(html, /24 个装配步骤 \+ 19 个真机门/);
  assert.match(html, /15 \/ 15额定筛选通过，仍HOLD/);
  assert.match(html, /BB8_阶段17_驱动电源器件选型门\.md/);
  assert.match(html, /power_component_candidates\.json/);
  assert.match(html, /power_component_selection_results\.json/);
  assert.match(html, /PWM低是制动而非隔离/);
  assert.match(html, /8件布局通过，12门未冻结/);
  assert.match(html, /HOLD_PHYSICAL_FIT_AND_INTERFACE_VALIDATION_REQUIRED/);
  assert.match(html, /BB8_阶段18_模块化驱动电源舱布局门\.md/);
  assert.match(html, /BB8_stage18_modular_drive_power_cassette_layout_gate\.md/);
  assert.match(html, /stage18_power_cassette_layout\.json/);
  assert.match(html, /stage18_power_cassette_results\.json/);
  assert.match(html, /重开审计确认39个阶段18对象/);
  assert.match(html, /64 \/ 64逻辑组合通过，仍HOLD/);
  assert.match(html, /HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED/);
  assert.match(html, /BB8_阶段19_独立双许可PWM硬件门\.md/);
  assert.match(html, /BB8_stage19_independent_dual_permissive_pwm_gate\.md/);
  assert.match(html, /stage19_dual_permissive_gate_contract\.json/);
  assert.match(html, /stage19_blender_reopen_audit\.json/);
  assert.match(html, /stage19_gate_truth_table\.csv/);
  assert.match(html, /stage19_gate_board_envelope\.scad/);
  assert.match(html, /冻结 1:1 尺寸基准/);
  assert.match(html, /BB8_stage8_exterior_topology\.md/);
  assert.match(html, /BB8_stage9_head_calibration\.md/);
  assert.match(html, /BB8_three_view_dimension_sheet\.png/);
  assert.match(html, /BB-8 Builders Club V3\.1/);
  assert.match(html, /装配章节导航/);
  assert.match(html, /视图缩放/);
  assert.match(html, /实际完成/);
  assert.match(html, /打开大图/);
  assert.match(html, /670/);
  assert.match(html, /标记本步骤完成/);
});

test("server-renders the complete English build guide", async () => {
  const response = await render("/en");
  assert.equal(response.status, 200);
  const html = await response.text();
  assert.match(html, /Turn the screen droid/);
  assert.match(html, /GitHub repository/);
  assert.match(html, /https:\/\/github\.com\/zhangyinxina-ui\/bb8-do-assembly-guide/);
  assert.match(html, /386 total objects and 182 internal objects/);
  assert.match(html, /150 fabrication objects, nine non-fabrication engineering markers and 23 non-fabrication pre-CAD gate references/);
  assert.match(html, /8\.463 kg nominal/);
  assert.match(html, /56\.2 mm nominal CoM/);
  assert.match(html, /2\.07× torque margin/);
  assert.match(html, /4\.22° resultant lean/);
  assert.match(html, /No unpowered slope hold/);
  assert.match(html, /Currently 0 \/ 19/);
  assert.match(html, /Nineteen physical gates/);
  assert.match(html, /HOLD_PHYSICAL_TESTS_NOT_RUN/);
  assert.match(html, /BB8_stage16_physical_commissioning_evidence_gate\.md/);
  assert.match(html, /commissioning_test_plan\.json/);
  assert.match(html, /Telemetry parser/);
  assert.match(html, /Evidence verifier/);
  assert.match(html, /24 assembly steps plus 19 physical gates/);
  assert.match(html, /15 \/ 15 ratings pass, still HOLD/);
  assert.match(html, /BB8_stage17_drive_power_component_selection_gate\.md/);
  assert.match(html, /Selection HOLD result/);
  assert.match(html, /PWM-low means brake rather than isolation/);
  assert.match(html, /8 modules clear, 12 gates open/);
  assert.match(html, /BB8_stage18_modular_drive_power_cassette_layout_gate\.md/);
  assert.match(html, /Stage 18 HOLD result/);
  assert.match(html, /passes the Blender 5\.1\.2 close-and-reopen audit/);
  assert.match(html, /64 \/ 64 logic rows pass, still HOLD/);
  assert.match(html, /Stage 19 machine contract/);
  assert.match(html, /Stage 19 Blender reopen evidence/);
  assert.match(html, /64-row truth table/);
  assert.match(html, /OpenSCAD envelope/);
  assert.match(html, /Freeze the 1:1 dimensional baseline/);
  assert.match(html, /personal non-commercial/);
  assert.match(html, /26-line procurement gate/);
  assert.match(html, /D0\/D1 servo versus Serial0 pin contention/);
  assert.match(html, /v2.1 D2–D5 table versus v3.4.3 source mismatch/);
  assert.match(html, /All twelve control-page attachments are hash-audited locally/);
  assert.match(html, /All 22 AIO32 source files compile with ESP32 core 3\.3\.7/);
  assert.match(html, /41% flash and 15% RAM/);
  assert.match(html, /SensorLib as a handbook-omitted dependency/);
  assert.match(html, /do_aio32_firmware_compile\.json/);
  assert.match(html, /generic website v3.4 ZIP is still v3.4.0/);
  assert.match(html, /five numbered build episodes plus one tyre-printing video/);
  assert.match(html, /zero complete mechanical CAD\/STL files/);
  assert.match(html, /Denton V1 is listed under CC BY 4\.0/);
  assert.match(html, /head is missing and STEP files are pending/);
  assert.match(html, /JRIZZ\/Cults lists Fusion 360 F3Z, STL and Arduino sketches/);
  assert.match(html, /Purchase and acceptance of CULTS Private Use require explicit user confirmation/);
  assert.match(html, /about-300 mm, 32-file CC BY-NC-SA 4\.0 static model/);
  assert.match(html, /Gambody lists 116 STLs and a 518 mm articulated version/);
  assert.match(html, /BB8_stage14_mass_cg_inertia_validation\.md/);
  assert.match(html, /BB8_stage15_drive_power_dynamic_stability\.md/);
  assert.match(html, /wired tether/);
  assert.match(html, /Switch to Chinese/);
});

test("removes starter preview metadata and content", async () => {
  const [css, page, layout] = await Promise.all([
    readFile(new URL("../app/globals.css", import.meta.url), "utf8"),
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
  ]);
  assert.match(css, /--orange:\s*#ff4b13/);
  assert.match(page, /D-O \/ RESOURCE MAP/);
  assert.doesNotMatch(page, /SkeletonPreview|codex-preview/);
  assert.match(layout, /lang="zh-CN"/);
});
