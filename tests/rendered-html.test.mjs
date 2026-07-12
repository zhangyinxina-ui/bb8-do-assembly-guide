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
  assert.match(html, /508/);
  assert.match(html, /Printed Droid/);
  assert.doesNotMatch(html, /href=["']\/model\/BB8_1to1_screen_referenced\.blend/);
  assert.match(html, /BB8_internal_three_view\.png/);
  assert.match(html, /internal_assembly_manifest\.csv/);
  assert.match(html, /147个制造对象和3个非制造工程标记/);
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
  assert.match(html, /DO_resource_audit\.md/);
  assert.match(html, /do_resource_manifest\.json/);
  assert.match(html, /DO_self_build_route\.md/);
  assert.match(html, /do_self_build_bom\.csv/);
  assert.match(html, /D01–D16调试门/);
  assert.match(html, /MDD10A与两块MD10C的来源冲突/);
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
  assert.match(html, /24 个可验收步骤/);
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
  assert.match(html, /147 fabrication objects plus three non-fabrication engineering markers/);
  assert.match(html, /8\.463 kg nominal/);
  assert.match(html, /56\.2 mm nominal CoM/);
  assert.match(html, /2\.07× torque margin/);
  assert.match(html, /4\.22° resultant lean/);
  assert.match(html, /No unpowered slope hold/);
  assert.match(html, /all live hardware tests remain NOT_RUN/i);
  assert.match(html, /24 acceptance-gated steps/);
  assert.match(html, /Freeze the 1:1 dimensional baseline/);
  assert.match(html, /personal non-commercial/);
  assert.match(html, /zero complete mechanical CAD\/STL files/);
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
