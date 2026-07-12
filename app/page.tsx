"use client";

import { useEffect, useRef, useState } from "react";
import { assemblySteps } from "./data/assemblySteps";

const asset = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\/+/, "")}`;

const views = [
  { label: "正视图", src: asset("/model/bb8-front.png") },
  { label: "侧视图", src: asset("/model/bb8-side.png") },
  { label: "后视图", src: asset("/model/bb8-back.png") },
];

type AssemblyMedia = { label: string; src: string; alt: string; note: string };

const phaseMedia: Record<string, AssemblyMedia[]> = {
  "基准与制造": [
    { label: "正视", src: asset("/model/bb8-front.png"), alt: "BB-8 1:1 正视基准", note: "用正视图锁定头身轮廓、主眼位置和打印缩放。" },
    { label: "侧视", src: asset("/model/bb8-side.png"), alt: "BB-8 1:1 侧视基准", note: "用侧视图检查头体交叠、天线和球面面板包络。" },
    { label: "后视", src: asset("/model/bb8-back.png"), alt: "BB-8 1:1 后视基准", note: "用后视图核对后部检修板、缝线和后面板方向。" },
  ],
  "底盘": [
    { label: "正视", src: asset("/model/internal_front.png"), alt: "BB-8 内车正视图", note: "检查 310 mm 轮距、驱动轮接触和低重心布置。" },
    { label: "侧视", src: asset("/model/internal_side.png"), alt: "BB-8 内车侧视图", note: "检查驱动轴线、配重高度和球壳内侧避让。" },
    { label: "俯视", src: asset("/model/internal_top.png"), alt: "BB-8 内车俯视图", note: "检查左右电机、纵梁、线束与赤道维护区。" },
  ],
  "电气与配重": [
    { label: "侧视", src: asset("/model/internal_side.png"), alt: "BB-8 内部机构侧视图", note: "核对电池、控制托盘、线束弯曲半径和桅杆避让。" },
    { label: "俯视", src: asset("/model/internal_top.png"), alt: "BB-8 内部机构俯视图", note: "核对功率与信号分区，以及四个维护连接器的可达性。" },
  ],
  "磁头机构": [
    { label: "机构", src: asset("/model/bb8-mechanism.png"), alt: "BB-8 磁性头部机构", note: "核对 6+6 磁体、8 mm 气隙和三只头底滚轮。" },
    { label: "侧视", src: asset("/model/internal_side.png"), alt: "BB-8 桅杆与头部侧视图", note: "检查桅杆顶盘、磁体保持架和头部滚动包络。" },
  ],
  "关闭球壳": [
    { label: "侧视", src: asset("/model/bb8-side.png"), alt: "BB-8 合壳侧视图", note: "闭合赤道缝后检查头身间隙、面板接缝和滚动包络。" },
    { label: "后视", src: asset("/model/bb8-back.png"), alt: "BB-8 合壳后视图", note: "复核后部外观件、赤道错台和检修方向。" },
  ],
  "烧录与标定": [
    { label: "三视图", src: asset("/model/BB8_internal_three_view.png"), alt: "BB-8 内部机构三视图", note: "架空标定前确认左右轮、IMU 轴向、急停和维护连接器。" },
    { label: "运动机构", src: asset("/model/bb8-mechanism.png"), alt: "BB-8 运动机构检查图", note: "低速试车前复核磁头耦合、驱动轮接触和安全包络。" },
  ],
};

const sources = [
  {
    name: "StarWars.com 制作访谈",
    tag: "官方事实",
    href: "https://www.starwars.com/news/droid-dreams-how-neal-scanlan-and-the-star-wars-the-force-awakens-team-brought-bb-8-to-life",
  },
  {
    name: "StarWars.com BB-8 资料库",
    tag: "官方高度 0.67 m",
    href: "https://www.starwars.com/databank/bb-8/",
  },
  {
    name: "BB-8 尺寸照片测量",
    tag: "社区测绘",
    href: "https://rimstar.org/science_electronics_projects/bb-8_dimensions.htm",
  },
  {
    name: "BB-8 Builders Club V3.1 面板方向指南",
    tag: "CC BY-NC-SA 4.0",
    href: "https://bb8builders.club/wiki/images/6/68/BB-8-V3-Panel-Orientation-Guide.pdf",
  },
  {
    name: "James Bruton BB-8 v2 CAD / Code",
    tag: "待核许可",
    href: "https://youtu.be/pgIGhuc5L3M",
  },
  {
    name: "Printed Droid D-O 总页",
    tag: "公开资料",
    href: "https://www.printed-droid.com/kb/d-o/",
  },
  {
    name: "D-O 装配手册",
    tag: "免费阅读",
    href: "https://d-o.dozuki.com/c/D-O_Assembly",
  },
  {
    name: "D-O 控制程序",
    tag: "个人非商业许可",
    href: "https://github.com/PrintedDroid/D-O-Printed-Droid",
  },
  {
    name: "Mantis Hacks D-O 系列",
    tag: "视频 / BOM",
    href: "https://youtube.com/playlist?list=PLTSAQ5KEjPVCldgA1t-KT1lRTKJdAY7er",
  },
  {
    name: "Mr Baddeley D-O V2",
    tag: "Patreon 付费",
    href: "https://www.patreon.com/mrbaddeley",
  },
];

export default function Home() {
  const [view, setView] = useState(0);
  const [step, setStep] = useState(0);
  const [completed, setCompleted] = useState<string[]>([]);
  const [assemblyZoom, setAssemblyZoom] = useState(100);
  const [assemblyView, setAssemblyView] = useState(0);
  const mediaDialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    const saved = Number(window.localStorage.getItem("bb8-assembly-step"));
    if (Number.isInteger(saved) && saved >= 0 && saved < assemblySteps.length) {
      window.queueMicrotask(() => setStep(saved));
    }
  }, []);
  useEffect(() => {
    window.localStorage.setItem("bb8-assembly-step", String(step));
  }, [step]);
  useEffect(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem("bb8-completed-steps") ?? "[]");
      if (Array.isArray(saved)) {
        window.queueMicrotask(() => setCompleted(saved.filter((id) => typeof id === "string")));
      }
    } catch { /* Keep the empty default when stored data is invalid. */ }
  }, []);
  useEffect(() => {
    window.localStorage.setItem("bb8-completed-steps", JSON.stringify(completed));
  }, [completed]);
  const activeStep = assemblySteps[step];
  const activeMediaOptions = phaseMedia[activeStep.phase];
  const activeMedia = activeMediaOptions[assemblyView] ?? activeMediaOptions[0];
  const completionPercent = (completed.length / assemblySteps.length) * 100;
  const isCompleted = completed.includes(activeStep.id);
  const toggleCompleted = () => {
    setCompleted((current) => isCompleted
      ? current.filter((id) => id !== activeStep.id)
      : [...current, activeStep.id]);
  };
  const changeStep = (nextStep: number) => {
    setStep(nextStep);
    setAssemblyView(0);
    setAssemblyZoom(100);
  };
  return (
    <main>
      <nav className="nav">
        <a className="brand" href="#top">
          <span>R</span>EP·LAB
        </a>
        <div>
          <a href="#model">BB-8</a>
          <a href="#do">D-O</a>
          <a href="#build">装配</a>
          <a href="#sources">来源</a>
        </div>
      </nav>
      <section className="hero" id="top">
        <div className="eyebrow">SCREEN-REFERENCED · 1:1 BUILD</div>
        <h1>
          把银幕机器人
          <br />
          <em>做成真正的机器。</em>
        </h1>
        <p>
          一套面向个人制作者的 BB-8 参数化模型、D-O
          资源地图与安全装配指南。事实、推测和付费资源被严格分开。
        </p>
        <div className="hero-actions">
          <a className="button primary" href="#model">
            查看三视图与模型证据
          </a>
          <a className="button" href="#build">
            开始装配 ↓
          </a>
        </div>
        <div className="metrics">
          <div>
            <b>508</b>
            <span>mm 球体直径</span>
          </div>
          <div>
            <b>295</b>
            <span>mm 头部直径</span>
          </div>
          <div>
            <b>670</b>
            <span>mm 无天线总高</span>
          </div>
        </div>
      </section>

      <section className="section model-section" id="model">
        <div className="section-head">
          <span>01 / BB-8 DIGITAL TWIN</span>
          <h2>
            三视图共用一套
            <br />
            可编辑的 1:1 几何
          </h2>
          <p>
            官方资料库给出的角色高度为 0.67 m；508 mm 球体和 295 mm
            头部来自照片测量与社区全尺寸复刻，不是 Lucasfilm 官方 CAD。天线保留为参数化待校准件。
          </p>
        </div>
        <div className="viewer">
          <div className="tabs">
            {views.map((v, i) => (
              <button
                key={v.label}
                className={view === i ? "active" : ""}
                onClick={() => setView(i)}
              >
                {v.label}
              </button>
            ))}
          </div>
          <img src={views[view].src} alt={`BB-8 ${views[view].label}`} />
          <div className="scale">
            <span>0</span>
            <i></i>
            <span>508 mm</span>
          </div>
        </div>
      </section>

      <section className="section structure">
        <div className="section-head">
          <span>02 / ARCHITECTURE</span>
          <h2>可组装的复刻架构</h2>
        </div>
        <div className="cards">
          <article>
            <b>A</b>
            <h3>球壳与面板</h3>
            <p>两片 20 英寸级球壳，面板、检修口和耐磨接触面分层处理。</p>
          </article>
          <article>
            <b>B</b>
            <h3>低重心内车</h3>
            <p>双轮差速驱动，电池与配重低置，IMU 管理姿态和失控保护。</p>
          </article>
          <article>
            <b>C</b>
            <h3>磁性头部</h3>
            <p>
              内部顶置磁铁与头底滚轮随动；属于社区复刻方案，并非已公开的电影原机。
            </p>
          </article>
        </div>
        <div className="mechanism">
          <img
            src={asset("/model/BB8_internal_three_view.png")}
            alt="BB-8 内部机构正视、侧视和俯视三视图"
          />
          <div>
            <span className="kicker">BUILDABLE CORE</span>
            <h3>
              内车是可编辑对象，
              <br />
              不是一张概念图。
            </h3>
            <p>
              Blender
              文件内已有88个带稳定标记的内部对象。驱动轮和四只稳定球实际到达254 mm内壳；
              IG42E-24K按125.2 mm总长、PCD 35 mm安装孔和310 mm轮距布置，两台电机不再互相穿透。
              赤道维护接口包含494 mm密封圈、8个锁扣，并明确建模12段动力/编码器线束和4个可断开连接器。
              磁性头部采用6+6磁体包络、8 mm总气隙和3只24 mm头底滚轮，装机拉力验收线为40 N。
            </p>
            <div className="doc-actions">
              <a className="button" href={asset("/downloads/BB8_BOM.md")} download>
                下载 BB-8 BOM
              </a>
              <a className="button" href={asset("/downloads/internal_assembly_manifest.csv")} download>
                下载装配尺寸清单
              </a>
              <a className="button" href={asset("/downloads/BB8_motor_selection.md")} download>
                下载真实电机选型报告
              </a>
              <a className="button" href={asset("/downloads/BB8_stage5_motor_install.md")} download>
                下载电机安装与拆装步骤
              </a>
              <a className="button" href={asset("/downloads/BB8_stage6_shell_harness.md")} download>
                下载球壳与线束维护步骤
              </a>
              <a className="button" href={asset("/downloads/BB8_magnetic_coupling.md")} download>
                下载磁性头部耦合验证
              </a>
              <a className="button" href={asset("/downloads/BB8_stage8_exterior_topology.md")} download>
                下载外观拓扑与尺寸依据
              </a>
              <a className="button" href={asset("/downloads/BB8_stage9_head_calibration.md")} download>
                下载 670 mm 头部校准记录
              </a>
              <a className="button" href={asset("/model/BB8_three_view_dimension_sheet.png")} download>
                下载最新三视图尺寸图
              </a>
              <a
                className="button"
                href="https://github.com/XRobots/BB82_public"
                target="_blank"
                rel="noreferrer"
              >
                James Bruton CAD/代码 ↗
              </a>
            </div>
          </div>
        </div>
        <div className="motion-lab">
          <div>
            <span className="kicker">KINEMATIC PROOF / 120 FRAMES</span>
            <h3>球壳滚动，<br />内车不跟着翻。</h3>
            <p>动画锁定 <code>s = Rθ</code>：球体一周位移 1.595929 m，96 mm 驱动轮转 5.291667 圈。内车只显示加速/制动俯仰，头部保持世界竖直目标。</p>
            <div className="download-grid">
              <a href={asset("/model/BB8_1to1_kinematic.glb")} download>GLB 动画模型</a>
              <a href={asset("/model/BB8_internal_mechanism_mm.stl")} download>内部机构 STL</a>
              <a href={asset("/downloads/BB8_kinematics.md")} download>运动学说明</a>
              <a href={asset("/downloads/kinematics.csv")} download>120 帧校验数据</a>
            </div>
          </div>
          <video controls autoPlay loop muted playsInline poster={asset("/model/bb8-front.png")}>
            <source src={asset("/model/BB8_kinematic_cycle.mp4")} type="video/mp4" />
          </video>
        </div>
      </section>

      <section className="section firmware-section" id="control">
        <div className="section-head">
          <span>03 / MOTION CONTROLLER</span>
          <h2>不只会动，<br />还必须会停。</h2>
          <p>控制核心、双正交编码器和 MPU6050 适配均已通过 ESP32-S3 编译：编码器轮速 PI、IMU 偏航修正与七条锁存安全联锁已接入同一控制循环。实体接线、参数标定和带电台架仍是落地门槛。</p>
        </div>
        <div className="control-grid">
          <article><span>01</span><h3>200 Hz 闭环速度</h3><p>左右编码器轮速进入 PI，IMU 偏航率修正差动目标；直线巡航 RMS 误差 0.00772 m/s。</p></article>
          <article><span>02</span><h3>7 类故障锁存</h3><p>新增传感器过期与 IMU/编码器不一致；任一安全故障在当前控制周期撤销左右 PWM。</p></article>
          <article><span>03</span><h3>91.20° 动态转弯</h3><p>含电机惯性、滚阻、编码器量化和电池压降的闭环场景完成 91.20° 转弯。</p></article>
          <article><span>04</span><h3>行驶中失效停车</h3><p>0.20 m/s 重新起步后注入 IMU 过期，PWM 同周期归零，0.8 s 后速度 0.00224 m/s。</p></article>
          <article><span>05</span><h3>传感器默认拒动</h3><p>编码器 CPR 默认为0且每次上电必须显式配置；MPU6050 完成400个静止样本前，驱动EN保持关闭。</p></article>
        </div>
        <div className="firmware-downloads">
          <a href={asset("/downloads/BB8_controller_core.zip")} download>下载 C++ 控制核心</a>
          <a href={asset("/downloads/BB8_ESP32_S3_firmware.zip")} download>下载 ESP32-S3 固件草案</a>
          <a href={asset("/downloads/BB8_controller_README.md")} download>ESP32 适配与引脚合同</a>
          <a href={asset("/downloads/differential_turn.csv")} download>下载转弯校验 CSV</a>
          <a href={asset("/downloads/BB8_closed_loop_simulation.md")} download>下载阶段 10 闭环验证</a>
          <a href={asset("/downloads/closed_loop_telemetry.csv")} download>下载 200 Hz 闭环遥测</a>
          <a href={asset("/downloads/bb8_firmware_compile.json")} download>下载 ESP32 编译证据</a>
          <a href={asset("/downloads/BB8_stage11_sensor_adapter.md")} download>下载阶段 11 传感器适配</a>
          <a href={asset("/downloads/sensor_adapter_contract.json")} download>下载传感器接口合同</a>
        </div>
      </section>

      <section className="section firmware-section" id="physics">
        <div className="section-head">
          <span>04 / PHYSICS GATE</span>
          <h2>先算清楚，<br />再让它落地跑。</h2>
          <p>阶段 1 解析模型已覆盖球壳转动惯量、滚阻、双轮扭矩、轮壳附着、摆体回复力矩和磁头冲击保持。当前 PASS 只针对可追溯假设参数，不替代实物台架。</p>
        </div>
        <div className="control-grid">
          <article><span>01</span><h3>0.286 N·m / 电机</h3><p>6 kg、1 m/s² 设计点，含球壳转动惯量与滚阻；0.6 N·m 连续额定仅有 2.10× 理论裕量。</p></article>
          <article><span>02</span><h3>13.08× 附着裕量</h3><p>按 μ=0.7、每轮 80 N 预紧计算；必须用实际壳材和拉力计重新测量。</p></article>
          <article><span>03</span><h3>2.51× 磁保持裕量</h3><p>0.65 kg 头部、2.5g 垂向冲击需要 15.9 N；设计假设保持力 40 N。</p></article>
          <article><span>04</span><h3>低电量必须降额</h3><p>阶段 2 计算显示峰值 21 A 在低电量会降至 12.55 V；控制核心已加入 13.2–14.3 V 连续功率限制。</p></article>
          <article><span>05</span><h3>转弯合载荷 2.31×</h3><p>1 m/s、0.6 rad/s 转弯并叠加横向与垂向冲击，40 N 磁保持的解析裕量为 2.31×。</p></article>
          <article><span>06</span><h3>结构与热</h3><p>桅杆静态屈服裕量 18.52×；设计点电机集总稳态温度估算 38.9 °C，仍需实物模态和热试验。</p></article>
        </div>
        <div className="firmware-downloads">
          <a href={asset("/downloads/BB8_physics_validation.md")} download>下载物理验证报告</a>
          <a href={asset("/downloads/physics_inputs.json")} download>下载可修改参数</a>
          <a href={asset("/downloads/physics_sweep.csv")} download>下载 0–2 m/s² 扫描</a>
          <a href={asset("/downloads/BB8_multibody_validation.md")} download>下载阶段 2 多体验证</a>
          <a href={asset("/downloads/turning_multibody_sweep.csv")} download>下载转弯多体扫描</a>
        </div>
      </section>

      <section className="section do-section" id="do">
        <div className="do-copy">
          <span className="kicker">D-O / RESOURCE MAP</span>
          <h2>
            开源，
            <br />
            不等于“网上能看到”。
          </h2>
          <p>
            目前未找到可免费再分发的 D-O 整机机械包。但装配、接线、BOM
            和受个人非商业许可约束的控制源码，已经可以组成一条可审计的个人制作路线。
            现有24项采购状态表和D01–D16调试门；MDD10A与两块MD10C的来源冲突、
            电机/舵机负载和电源保护未冻结前，相关零件明确暂缓购买。
          </p>
        </div>
        <div className="do-grid">
          <div>
            <span>MECHANICAL CAD</span>
            <strong>付费</strong>
            <p>Mr Baddeley D-O V2 STL / Fusion，Patreon 会员资源。</p>
          </div>
          <div>
            <span>CONTROL CODE</span>
            <strong>已固定版本</strong>
            <p>v3.4.3 固定到 e90aacd；README 允许个人非商业使用、修改和分发，须保留声明与署名。Mega 2560 真编译通过：Flash 17%，RAM 18%。</p>
          </div>
          <div>
            <span>ASSEMBLY</span>
            <strong>免费</strong>
            <p>Printed Droid 两份 PDF 已校验哈希；公开仓库含5个 Arduino 草图，但整机机械 CAD/STL 为0。另有一个60 mm无轮调试支架，许可未明确，未在网站再分发。</p>
          </div>
          <div>
            <span>MANTIS HACKS</span>
            <strong>参考</strong>
            <p>六集开发记录与 BOM，未见 Matt 改版 CAD/程序下载。</p>
            <a
              className="inline-download"
              href={asset("/downloads/DO_resources.md")}
              download
            >
              下载完整资源索引 ↓
            </a>
            <a
              className="inline-download"
              href={asset("/downloads/DO_resource_audit.md")}
              download
            >
              下载自组入口与审计说明 ↓
            </a>
            <a
              className="inline-download"
              href={asset("/downloads/do_resource_manifest.json")}
              download
            >
              下载机器可读清单 ↓
            </a>
            <a
              className="inline-download"
              href={asset("/downloads/DO_self_build_route.md")}
              download
            >
              下载D01–D16自组调试路线 ↓
            </a>
            <a
              className="inline-download"
              href={asset("/downloads/do_self_build_bom.csv")}
              download
            >
              下载24项采购门控BOM ↓
            </a>
          </div>
        </div>
      </section>

      <section className="section build" id="build">
        <div className="section-head">
          <span>05 / EXECUTABLE ASSEMBLY</span>
          <h2>24 个可验收步骤，从模型到可控机器</h2>
          <p>进度保存在本机浏览器。每一步均给出零件、工具、动作与验收门槛；实物尺寸和安全限值仍须用采购件复测。</p>
        </div>
        <div className="progress-summary" aria-label="装配进度">
          <div><span>当前位置</span><b>{step + 1} / {assemblySteps.length}</b></div>
          <div><span>实际完成</span><b>{completed.length} / {assemblySteps.length}</b></div>
        </div>
        <div className="progress position-progress" title="当前位置">
          <i style={{ width: `${((step + 1) / assemblySteps.length) * 100}%` }}></i>
        </div>
        <div className="progress completion-progress" title="实际完成率">
          <i style={{ width: `${completionPercent}%` }}></i>
        </div>
        <div className="assembly-phases" aria-label="装配章节导航">
          {Object.keys(phaseMedia).map((phase) => {
            const first = assemblySteps.findIndex((item) => item.phase === phase);
            const phaseSteps = assemblySteps.filter((item) => item.phase === phase);
            const count = phaseSteps.filter((item) => completed.includes(item.id)).length;
            return (
              <button key={phase} className={activeStep.phase === phase ? "active" : ""} onClick={() => changeStep(first)}>
                {phase}<small>{count}/{phaseSteps.length}</small>
              </button>
            );
          })}
        </div>
        <div className="assembly-media">
          <div className="assembly-media-frame">
            <img src={activeMedia.src} alt={activeMedia.alt} style={{ transform: `scale(${assemblyZoom / 100})` }} />
          </div>
          <div className="assembly-media-controls">
            <b>{activeStep.phase} · {activeMedia.label}</b>
            <p>{activeMedia.note}</p>
            <div className="assembly-view-tabs" aria-label="当前步骤可用视图">
              {activeMediaOptions.map((media, index) => (
                <button key={media.label} type="button" className={assemblyView === index ? "active" : ""} onClick={() => setAssemblyView(index)}>
                  {media.label}
                </button>
              ))}
            </div>
            <label htmlFor="assembly-zoom">视图缩放：{assemblyZoom}%</label>
            <input id="assembly-zoom" type="range" min="80" max="180" value={assemblyZoom} onChange={(event) => setAssemblyZoom(Number(event.target.value))} />
            <div className="assembly-media-actions">
              <button type="button" onClick={() => setAssemblyZoom(100)}>重置视图</button>
              <button type="button" onClick={() => mediaDialog.current?.showModal()}>打开大图</button>
            </div>
          </div>
        </div>
        <dialog className="assembly-dialog" ref={mediaDialog}>
          <button type="button" aria-label="关闭大图" onClick={() => mediaDialog.current?.close()}>关闭 ×</button>
          <img src={activeMedia.src} alt={activeMedia.alt} />
          <p>{activeMedia.note}</p>
        </dialog>
        <div className="step-card">
          <div className="step-no">{String(step + 1).padStart(2, "0")}</div>
          <div>
            <small>
              {activeStep.phase} · {activeStep.id} · STEP {step + 1} OF {assemblySteps.length}
            </small>
            <h3>{activeStep.title}</h3>
            <dl className="step-detail">
              <div><dt>零件</dt><dd>{activeStep.parts}</dd></div>
              <div><dt>工具</dt><dd>{activeStep.tools}</dd></div>
              <div><dt>动作</dt><dd>{activeStep.action}</dd></div>
              <div><dt>验收</dt><dd>{activeStep.acceptance}</dd></div>
            </dl>
            {activeStep.warning && <p className="step-warning">安全：{activeStep.warning}</p>}
            <button type="button" className={`step-complete ${isCompleted ? "done" : ""}`} onClick={toggleCompleted}>
              {isCompleted ? "✓ 本步骤已完成" : "标记本步骤完成"}
            </button>
            <div className="step-nav">
              <button disabled={step === 0} onClick={() => changeStep(step - 1)}>
                ← 上一步
              </button>
              <button
                disabled={step === assemblySteps.length - 1}
                onClick={() => changeStep(step + 1)}
              >
                下一步 →
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="section sources" id="sources">
        <div className="section-head">
          <span>05 / SOURCES & LICENSE</span>
          <h2>
            你能用什么，
            <br />
            边界在哪里
          </h2>
        </div>
        <div className="source-list">
          {sources.map((s, i) => (
            <a href={s.href} target="_blank" rel="noreferrer" key={s.name}>
              <span>{String(i + 1).padStart(2, "0")}</span>
              <b>{s.name}</b>
              <em>{s.tag}</em>
              <i>↗</i>
            </a>
          ))}
        </div>
      </section>
      <footer>
        <p>
          非官方粉丝研究与个人教育原型。STAR WARS、BB-8、D-O
          及相关角色归权利人所有。请在打印、改作或再分发前逐项检查许可证。
        </p>
        <b>REP·LAB / BUILD LOG 001</b>
      </footer>
    </main>
  );
}
