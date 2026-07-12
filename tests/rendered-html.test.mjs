import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const developmentPreviewMeta =
  /<meta(?=[^>]*\bname=["']codex-preview["'])(?=[^>]*\bcontent=["']development["'])[^>]*>/i;

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);

  return worker.fetch(
    new Request("http://localhost/", {
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
  assert.match(html, /88个带稳定标记的内部对象/);
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
  assert.match(html, /ESP32-S3 适配草案均已编译/);
  assert.match(html, /BB8_physics_validation\.md/);
  assert.match(html, /0\.286 N·m/);
  assert.match(html, /2\.51× 磁保持裕量/);
  assert.match(html, /BB8_multibody_validation\.md/);
  assert.match(html, /12\.55 V/);
  assert.match(html, /转弯合载荷 2\.31×/);
  assert.match(html, /differential_turn\.csv/);
  assert.match(html, /7 类故障锁存/);
  assert.match(html, /BB8_closed_loop_simulation\.md/);
  assert.match(html, /closed_loop_telemetry\.csv/);
  assert.match(html, /bb8_firmware_compile\.json/);
  assert.match(html, /0\.00772 m\/s/);
  assert.match(html, /91\.20° 动态转弯/);
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
