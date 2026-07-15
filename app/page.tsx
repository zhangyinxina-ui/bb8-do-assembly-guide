"use client";

import { useEffect, useRef, useState } from "react";
import { assemblySteps } from "./data/assemblySteps";

const asset = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\/+/, "")}`;
const repositoryUrl = "https://github.com/zhangyinxina-ui/bb8-do-assembly-guide";

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
    name: "TI SN74LVC2G08 数据表",
    tag: "阶段19逻辑门一手资料",
    href: "https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf",
  },
  {
    name: "Vishay VO617A 数据表",
    tag: "阶段19光耦一手资料",
    href: "https://www.vishay.com/docs/83430/vo617a.pdf",
  },
  {
    name: "Cytron MDD20A 产品页",
    tag: "阶段19驱动接口资料",
    href: "https://sg.cytron.io/p-20amp-6v-30v-dc-motor-driver-2-channels",
  },
  {
    name: "JST XH 官方目录",
    tag: "阶段19连接器包络",
    href: "https://www.jst-mfg.com/product/pdf/eng/eXH.pdf",
  },
  {
    name: "Kaiser 6061-T6/T651 材料数据",
    tag: "阶段20结构筛查一手资料",
    href: "https://online.kaiseraluminum.com/depot/PublicProductInformation/Document/1015/Kaiser_Aluminum_6061_Sheet_Coil_and_Plate.pdf",
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
    name: "Denton V1 D-O",
    tag: "Thingiverse / CC BY 4.0 / WIP",
    href: "https://www.thingiverse.com/thing:4189546",
  },
  {
    name: "WF3D D-O 静态模型",
    tag: "Printables / CC BY-NC-SA 4.0",
    href: "https://www.printables.com/model/147063-star-wars-d-o-droid",
  },
  {
    name: "D-O Home Decor WIP",
    tag: "Printables / CC BY-NC 4.0",
    href: "https://www.printables.com/model/1269542-d-o-droid-star-wars-home-decor",
  },
  {
    name: "JRIZZ D-O 可动开发版",
    tag: "Cults / 付费私用",
    href: "https://cults3d.com/en/3d-model/gadget/d-o-droid-star-wars-droid",
  },
  {
    name: "Gambody D-O Assembly + Action",
    tag: "付费关节模型 / 非控制包",
    href: "https://www.gambody.com/premium/d-o-droid",
  },
  {
    name: "MakerWorld D-O 23859",
    tag: "待核验 / 不作为开源依据",
    href: "https://makerworld.com/en/models/23859-star-wars-d-o-droid",
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
          <a className="language-link" href={asset("/en/")} aria-label="Switch to English">EN</a>
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
          <a className="button" href={repositoryUrl} target="_blank" rel="noreferrer">
            GitHub 项目 ↗
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
              文件内重开审计确认386个总对象、182个内部对象：150个制造对象、9个非制造工程标记和23个阶段19非制造预CAD参考对象。驱动轮和四只稳定球实际到达254 mm内壳；
              IG42E-24K按125.2 mm总长、PCD 35 mm安装孔和310 mm轮距布置，两台电机不再互相穿透。
              赤道维护接口包含494 mm密封圈、8个锁扣，并明确建模12段动力/编码器线束和4个可断开连接器。
              磁性头部采用6+6磁体包络、8 mm总气隙和3只24 mm头底滚轮，装机拉力验收线为40 N。
              电子托盘另有双INA226、双2 mΩ四线分流器、6个M2.5支柱和独立SAFE_A/SAFE_B/ALERT_N→PWM门的预CAD包络；真实带电试验仍为NOT_RUN。
              阶段14新增120 × 70 × 24 mm、名义1.50 kg的密封低位钢配重盒，并用17组质量账本替代未经证明的110 mm质心假设。
              阶段15再加入左右电机驱动器、散热器、主保险丝、常开接触器、双通道常闭急停、安全继电器、维护断电和系留急停插口；30个新对象全部随内车运动，器件型号与电流额定仍保持未冻结。
              阶段16不伪造新的几何完成度，而是把19项真机调试门、真实文件哈希和测量限值接到同一工程证据链；当前为0/19通过。
              阶段17用厂商官方资料筛选MDD20A、30 A MIDI保险丝、SW60接触器和P28A 4S2P电池候选：15/15额定检查通过，但独立去能、再生、堵转、BMS和电池包仍未冻结，不能采购放行。
              阶段18已把REC Active BMS 4S、MDD20A、SW60、MIDI保险丝、外置分流器和双通道门板的模块化电源舱写入唯一Blender主工程；重开审计确认39个阶段18对象、150个制造对象和9个工程标记。8个候选包络通过数字间隙门，12项实物冻结门仍未通过，不能把解析几何描述成实物装配完成。
              阶段19进一步发布双许可PWM门合同，并把23个板件/器件参考包络写入同一主工程；关闭重开后的Blender 5.1.2审计确认386个总对象和182个内部对象，制造清单仍严格保持150项。SAFE_A、SAFE_B、双INA226 ALERT_N和3.3 V逻辑电源任一失效都会解析拉低左右PWM；64组真值表全部通过。正式KiCad 10原理图为0项ERC违规；50 × 35 mm两层PCB已布线，0项DRC违规、0个未连接项，34个器件引用、91条规范引脚连接和21个网络完成双重交叉审计。独立原理图/布局同行复核、Gerber/钻孔发布复核和台架波形仍缺失，不能制造或上电。
              阶段20把结构解析重新绑定到当前制造清单：当前桅杆是Ø24 × 340 mm，旧阶段2的Ø12/Ø8 × 300 mm结论已明确标为不再代表当前模型。2.5 g垂向、1.0 g侧向、斜撑屈曲、桅杆模态和理想基材疲劳筛查通过，但轮—壳接触仍缺5.5 mm径向调节预算，15项材料、连接、公差和实物门未关闭；当前状态为HOLD_JOINT_TOLERANCE_MATERIAL_AND_PHYSICAL_VALIDATION_REQUIRED。
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
              <a className="button" href={asset("/downloads/BB8_stage13_power_hardware.md")} download>
                下载阶段 13 保护硬件建模
              </a>
              <a className="button" href={asset("/downloads/BB8_阶段14_质量质心与惯量验证.md")} download>
                下载阶段 14 质量/质心验证
              </a>
              <a className="button" href={asset("/downloads/BB8_stage14_mass_cg_inertia_validation.md")} download>
                Download Stage 14 English report
              </a>
              <a className="button" href={asset("/downloads/BB8_阶段15_驱动电源与动态稳定性.md")} download>
                下载阶段 15 驱动电源与稳定性
              </a>
              <a className="button" href={asset("/downloads/BB8_stage15_drive_power_dynamic_stability.md")} download>
                Download Stage 15 English report
              </a>
              <a className="button" href={asset("/downloads/BB8_阶段16_真机调试证据门.md")} download>
                下载阶段 16 真机调试证据门
              </a>
              <a className="button" href={asset("/downloads/BB8_stage16_physical_commissioning_evidence_gate.md")} download>
                Download Stage 16 English report
              </a>
              <a className="button" href={asset("/downloads/BB8_阶段17_驱动电源器件选型门.md")} download>
                下载阶段 17 电源器件选型门
              </a>
              <a className="button" href={asset("/downloads/BB8_stage17_drive_power_component_selection_gate.md")} download>
                Download Stage 17 English report
              </a>
              <a className="button" href={asset("/downloads/BB8_阶段18_模块化驱动电源舱布局门.md")} download>
                下载阶段 18 模块化电源舱报告
              </a>
              <a className="button" href={asset("/downloads/BB8_stage18_modular_drive_power_cassette_layout_gate.md")} download>
                Download Stage 18 English report
              </a>
              <a className="button" href={asset("/downloads/BB8_阶段19_独立双许可PWM硬件门.md")} download>
                下载阶段 19 双许可 PWM 门报告
              </a>
              <a className="button" href={asset("/downloads/BB8_stage19_independent_dual_permissive_pwm_gate.md")} download>
                Download Stage 19 English report
              </a>
              <a className="button" href={asset("/downloads/stage19_blender_reopen_audit.json")} download>
                下载 Stage 19 Blender 重开证据
              </a>
              <a className="button" href={asset("/downloads/BB8_阶段20_结构载荷与公差门.md")} download>
                下载阶段 20 结构载荷与公差报告
              </a>
              <a className="button" href={asset("/downloads/BB8_stage20_structural_load_and_tolerance_gate.md")} download>
                Download Stage 20 English report
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
        <div className="mechanism pcb-evidence">
          <img
            src={asset("/images/BB8_stage19_gate_pcb_isometric.png")}
            alt="BB-8 阶段19双许可PWM门50乘35毫米两层PCB等轴测复核图"
          />
          <div>
            <span className="kicker">STAGE 19 / ROUTED PCB DRC EVIDENCE</span>
            <h3>布线已经完成，<br />制造仍未放行。</h3>
            <p>
              KiCad 10.0.4对跟踪板和临时重生成板均报告0项DRC违规、0个未连接项。
              结构核验覆盖38个封装、91条规范引脚连接、21个命名网络、1614段走线、54个过孔、
              F.Cu 3V3与B.Cu GND铜区，以及四个合同坐标上的Ø3.2 mm非金属化安装孔。
              这些只证明数字CAD的一致性；没有独立同行复核、Gerber/钻孔发布、实板导通、上电或20 ms示波器证据。
            </p>
            <div className="doc-actions">
              <a className="button" href={asset("/downloads/stage19_dual_permissive_gate.kicad_pcb")} download>下载KiCad PCB</a>
              <a className="button" href={asset("/downloads/stage19_kicad_pcb_drc.json")} download>下载DRC 0违规报告</a>
              <a className="button" href={asset("/downloads/stage19_kicad_pcb_verification.json")} download>下载PCB结构核验</a>
              <a className="button" href={asset("/images/BB8_stage19_gate_pcb_top.png")} download>下载顶层复核图</a>
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
          <p>控制核心、双正交编码器、MPU6050 和双 INA226 适配均已通过 ESP32-S3 编译。阶段17确认MDD20A额定裕量足够，但其PWM低是制动而非隔离；阶段18把安全链写入可拆卸电源舱几何。阶段19现已冻结 `PWM_OUT = POWER ∧ PWM_IN ∧ SAFE_A ∧ SAFE_B ∧ ALERT_N` 的合同、64行真值表、正式KiCad 10原理图和两层布线PCB；ERC与DRC均为0项违规，PCB为0个未连接项，规范CSV与KiCad原理图/PCB双重交叉审计通过。真正撤销驱动母线仍由安全继电器和常开接触器完成，独立同行复核、Gerber/钻孔发布、实物装配、上电与真机验证仍待完成。</p>
        </div>
        <div className="control-grid">
          <article><span>01</span><h3>200 Hz 闭环速度</h3><p>左右编码器轮速进入 PI，IMU 偏航率修正差动目标；直线巡航 RMS 误差 0.00772 m/s。</p></article>
          <article><span>02</span><h3>11 类故障锁存</h3><p>新增电流传感器过期、硬件 ALERT、测量过流和持续堵转；任一故障同帧撤销 PWM 与 EN。</p></article>
          <article><span>03</span><h3>91.20° 动态转弯</h3><p>含电机惯性、滚阻、编码器量化和电池压降的闭环场景完成 91.20° 转弯。</p></article>
          <article><span>04</span><h3>行驶中失效停车</h3><p>0.20 m/s 重新起步后注入 IMU 过期，PWM 同周期归零，0.8 s 后速度 0.00224 m/s。</p></article>
          <article><span>05</span><h3>传感器默认拒动</h3><p>编码器 CPR 默认为0且每次上电必须显式配置；MPU6050 完成400个静止样本前，驱动EN保持关闭。</p></article>
          <article><span>06</span><h3>硬件急停去能</h3><p>双通道常闭回路驱动安全继电器与常开接触器；首次试验必须接有线系留急停，无线不能单独作为安全链。</p></article>
          <article><span>07</span><h3>真机证据不允许空PASS</h3><p>19项记录必须同时有实测数值、真实相对路径和匹配SHA-256；合成数据默认被审计器拒绝。</p></article>
          <article><span>08</span><h3>15 / 15额定筛选通过，仍HOLD</h3><p>MDD20A、MIDI、SW60和P28A的目录裕量通过；独立去能、再生、堵转、I²t和4S BMS未冻结。</p></article>
          <article><span>09</span><h3>8件布局通过，12门未冻结</h3><p>解析余量为球壳27.643 mm、候选件7.500 mm、既有机构6.000 mm；几何已写入并通过重开审计，实物接口结果仍为HOLD_PHYSICAL_FIT_AND_INTERFACE_VALIDATION_REQUIRED。</p></article>
          <article><span>10</span><h3>ERC/DRC均为0，仍HOLD</h3><p>64/64逻辑组合通过；两层PCB为0项违规、0个未连接项。没有独立同行复核、Gerber/钻孔发布、实板和台架波形，状态仍为HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED。</p></article>
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
          <a href={asset("/downloads/BB8_stage12_power_safety.md")} download>下载阶段 12 电流保护</a>
          <a href={asset("/downloads/power_safety_contract.json")} download>下载电流保护合同</a>
          <a href={asset("/downloads/power_safety_replay.csv")} download>下载 5 ms 故障回放</a>
          <a href={asset("/downloads/commissioning_test_plan.json")} download>下载19项真机测试矩阵</a>
          <a href={asset("/downloads/commissioning_evidence.json")} download>下载实物证据填写模板</a>
          <a href={asset("/downloads/commissioning_results.json")} download>下载当前验收状态</a>
          <a href={asset("/downloads/parse_bb8_telemetry.py")} download>下载真机遥测解析器</a>
          <a href={asset("/downloads/verify_commissioning_evidence.py")} download>下载证据审计器</a>
          <a href={asset("/downloads/BB8_阶段17_驱动电源器件选型门.md")} download>下载阶段17中文报告</a>
          <a href={asset("/downloads/BB8_stage17_drive_power_component_selection_gate.md")} download>下载阶段17英文报告</a>
          <a href={asset("/downloads/power_component_candidates.json")} download>下载器件候选矩阵</a>
          <a href={asset("/downloads/power_component_selection_results.json")} download>下载选型HOLD结果</a>
          <a href={asset("/downloads/verify_power_component_selection.py")} download>下载选型验证器</a>
          <a href={asset("/downloads/BB8_阶段18_模块化驱动电源舱布局门.md")} download>下载阶段18中文报告</a>
          <a href={asset("/downloads/BB8_stage18_modular_drive_power_cassette_layout_gate.md")} download>下载阶段18英文报告</a>
          <a href={asset("/downloads/stage18_layout_baseline.json")} download>下载阶段18只读布局基线</a>
          <a href={asset("/downloads/stage18_power_cassette_layout.json")} download>下载模块化电源舱布局</a>
          <a href={asset("/downloads/stage18_power_cassette_results.json")} download>下载阶段18 HOLD结果</a>
          <a href={asset("/downloads/verify_power_cassette_layout.py")} download>下载阶段18布局验证器</a>
          <a href={asset("/downloads/BB8_阶段19_独立双许可PWM硬件门.md")} download>下载阶段19中文报告</a>
          <a href={asset("/downloads/BB8_stage19_independent_dual_permissive_pwm_gate.md")} download>下载阶段19英文报告</a>
          <a href={asset("/downloads/stage19_dual_permissive_gate_contract.json")} download>下载阶段19机器合同</a>
          <a href={asset("/downloads/stage19_dual_permissive_gate_results.json")} download>下载阶段19 HOLD结果</a>
          <a href={asset("/downloads/stage19_blender_reopen_audit.json")} download>下载阶段19 Blender重开证据</a>
          <a href={asset("/downloads/stage19_gate_truth_table.csv")} download>下载64行真值表</a>
          <a href={asset("/downloads/stage19_gate_bom.csv")} download>下载门板预选BOM</a>
          <a href={asset("/downloads/stage19_gate_netlist.csv")} download>下载引脚网表</a>
          <a href={asset("/downloads/verify_dual_permissive_gate.py")} download>下载阶段19验证器</a>
          <a href={asset("/downloads/stage19_gate_board_envelope.scad")} download>下载门板OpenSCAD包络</a>
          <a href={asset("/downloads/stage19_kicad_project.zip")} download>下载完整KiCad参考工程</a>
          <a href={asset("/downloads/BB8_stage19_dual_permissive_gate_schematic.pdf")} download>下载原理图PDF</a>
          <a href={asset("/downloads/stage19_kicad_erc.json")} download>下载ERC 0违规报告</a>
          <a href={asset("/downloads/stage19_kicad_verification.json")} download>下载KiCad交叉审计结果</a>
          <a href={asset("/downloads/stage19_kicad_netlist.xml")} download>下载KiCad XML网表</a>
          <a href={asset("/downloads/stage19_kicad_bom.csv")} download>下载KiCad BOM</a>
          <a href={asset("/downloads/verify_stage19_kicad.py")} download>下载KiCad验证器</a>
          <a href={asset("/downloads/stage19_dual_permissive_gate.kicad_pcb")} download>下载两层布线PCB</a>
          <a href={asset("/downloads/stage19_kicad_pcb_drc.json")} download>下载PCB DRC报告</a>
          <a href={asset("/downloads/stage19_kicad_pcb_verification.json")} download>下载PCB结构核验</a>
          <a href={asset("/downloads/generate_stage19_kicad_pcb.py")} download>下载PCB生成器</a>
          <a href={asset("/downloads/verify_stage19_kicad_pcb.py")} download>下载PCB验证器</a>
          <a href={asset("/downloads/export_stage19_kicad_pcb.py")} download>下载PCB复核图导出器</a>
        </div>
      </section>

      <section className="section firmware-section" id="physics">
        <div className="section-head">
          <span>04 / PHYSICS GATE</span>
          <h2>先算清楚，<br />再让它落地跑。</h2>
          <p>阶段14以17组质量账本替代110 mm旧假设；阶段15加入动态稳定性；阶段16将解析门转换为19项真机测量合同。阶段17把目录额定与实测冻结分开，阶段18验证模块布局并写入主模型，阶段19补齐PWM门PCB证据，阶段20再把结构载荷绑定到当前制造清单并封锁旧桅杆几何漂移；这些都不等于PCB制造、器件采购、材料/连接冻结、实物试装、封壳热或整机运行通过。</p>
        </div>
        <div className="control-grid">
          <article><span>01</span><h3>8.463 kg 名义质量</h3><p>17组输入范围为6.375–10.628 kg；所有分组在实物称重前均保持NOT_RUN。</p></article>
          <article><span>02</span><h3>质心下置 56.2 mm</h3><p>名义z=-56.2 mm；穷举最不利质量角点后仍为z=-27.7 mm。</p></article>
          <article><span>03</span><h3>3°动态坡道点</h3><p>0.20 m/s²加速、0.30 m/s、0.80 m转弯半径时，每台需求0.289 N·m。</p></article>
          <article><span>04</span><h3>2.07× 连续扭矩裕量</h3><p>3°设计点刚超过2×门槛；0加速度的解析坡度上限约4.50°，不是实物认证。</p></article>
          <article><span>05</span><h3>4.22°合成倾角</h3><p>同时包含上坡、纵向加速与转弯侧向加速度，低于12°设计合同。</p></article>
          <article><span>06</span><h3>断电坡道不驻车</h3><p>当前没有机械驻车制动，断电后不能在坡道保持位置，必须用平地、支架或止轮措施。</p></article>
          <article><span>07</span><h3>19项强制真机门</h3><p>覆盖称重/质心、40 N磁头、电气去能、标定、堵转、热、地面、坡道、再生和维护。</p></article>
          <article><span>08</span><h3>当前0 / 19</h3><p>审计结果为HOLD_PHYSICAL_TESTS_NOT_RUN；没有真实硬件文件时，--require-pass必然失败。</p></article>
          <article><span>09</span><h3>旧桅杆结论已封锁</h3><p>当前是Ø24 × 340 mm包络；阶段2的Ø12/Ø8 × 300 mm弯曲结论不再代表主模型。</p></article>
          <article><span>10</span><h3>解析通过，公差仍HOLD</h3><p>2.5 g下纵梁22.814 MPa/0.670 mm，桅杆一阶估算40.47 Hz；但轮—壳径向调节短缺5.5 mm，15项冻结门未关闭。</p></article>
        </div>
        <div className="firmware-downloads">
          <a href={asset("/downloads/BB8_physics_validation.md")} download>下载物理验证报告</a>
          <a href={asset("/downloads/physics_inputs.json")} download>下载可修改参数</a>
          <a href={asset("/downloads/physics_sweep.csv")} download>下载 0–2 m/s² 扫描</a>
          <a href={asset("/downloads/BB8_multibody_validation.md")} download>下载阶段 2 多体验证</a>
          <a href={asset("/downloads/turning_multibody_sweep.csv")} download>下载转弯多体扫描</a>
          <a href={asset("/downloads/BB8_阶段14_质量质心与惯量验证.md")} download>下载阶段14质量报告</a>
          <a href={asset("/downloads/mass_properties_input.json")} download>下载17组质量输入</a>
          <a href={asset("/downloads/mass_properties_results.json")} download>下载质心惯量结果</a>
          <a href={asset("/downloads/mass_properties_scenarios.csv")} download>下载质量角点CSV</a>
          <a href={asset("/downloads/BB8_阶段15_驱动电源与动态稳定性.md")} download>下载阶段15中文报告</a>
          <a href={asset("/downloads/stability_envelope_input.json")} download>下载稳定性输入</a>
          <a href={asset("/downloads/stability_envelope_results.json")} download>下载稳定性结果</a>
          <a href={asset("/downloads/stability_envelope_sweep.csv")} download>下载坡度/加速度扫描</a>
          <a href={asset("/downloads/BB8_阶段16_真机调试证据门.md")} download>下载阶段16中文报告</a>
          <a href={asset("/downloads/BB8_stage16_physical_commissioning_evidence_gate.md")} download>下载阶段16英文报告</a>
          <a href={asset("/downloads/BB8_阶段17_驱动电源器件选型门.md")} download>下载阶段17中文报告</a>
          <a href={asset("/downloads/BB8_stage17_drive_power_component_selection_gate.md")} download>下载阶段17英文报告</a>
          <a href={asset("/downloads/power_component_selection_results.json")} download>下载阶段17结果</a>
          <a href={asset("/downloads/BB8_阶段18_模块化驱动电源舱布局门.md")} download>下载阶段18中文报告</a>
          <a href={asset("/downloads/BB8_stage18_modular_drive_power_cassette_layout_gate.md")} download>下载阶段18英文报告</a>
          <a href={asset("/downloads/stage18_power_cassette_results.json")} download>下载阶段18布局结果</a>
          <a href={asset("/downloads/BB8_阶段19_独立双许可PWM硬件门.md")} download>下载阶段19中文报告</a>
          <a href={asset("/downloads/BB8_stage19_independent_dual_permissive_pwm_gate.md")} download>下载阶段19英文报告</a>
          <a href={asset("/downloads/stage19_dual_permissive_gate_results.json")} download>下载阶段19门板结果</a>
          <a href={asset("/downloads/BB8_阶段20_结构载荷与公差门.md")} download>下载阶段20中文报告</a>
          <a href={asset("/downloads/BB8_stage20_structural_load_and_tolerance_gate.md")} download>下载阶段20英文报告</a>
          <a href={asset("/downloads/stage20_structural_load_contract.json")} download>下载阶段20机器合同</a>
          <a href={asset("/downloads/stage20_structural_load_results.json")} download>下载阶段20 HOLD结果</a>
          <a href={asset("/downloads/stage20_structural_load_sweep.csv")} download>下载结构载荷扫描</a>
          <a href={asset("/downloads/verify_stage20_structural_load_path.py")} download>下载阶段20验证器</a>
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
            目前仍未找到一个完整、可公开再分发、同时含机械、控制、电气和真机验证的 D-O 整机开源包。
            Denton V1 是免费 CC BY 4.0 可动候选，但页面仍写头部缺失、STEP 待发布，且 Baddeley 派生授权需复核；
            JRIZZ / Cults 更接近机械与 Arduino 整合包，但属于付费私用开发版且尚未购买验包。
            两个 Printables 条目是静态模型，Gambody 是付费关节/改装参考，不能冒充自平衡整机。
            装配、接线、BOM 和受个人非商业许可约束的 Printed Droid 控制源码，已经可以组成一条可审计的个人制作路线。
            现有26项采购状态表和D01–D16调试门；MDD10A与两块MD10C的来源冲突仍待硬件冻结。
            D0/D1舵机与Serial0的软件争用已经形成固定哈希的D22–D25安全变体和线束合同，并通过Mega编译；
            但实体导通、USB/串口、四路脉宽、电机/舵机负载和电源保护仍未验证，相关上电与采购继续门控。
          </p>
        </div>
        <div className="do-grid">
          <div>
            <span>FREE FUNCTIONAL WIP</span>
            <strong>免费但不完整</strong>
            <p>Denton V1 页面标 CC BY 4.0，称含分组件 STL 和 3D PDF；同时仍标注 WIP、头部缺失、STEP 待后续，文件包和派生授权尚未审计。</p>
            <a className="inline-download" href="https://www.thingiverse.com/thing:4189546" target="_blank" rel="noreferrer">查看原始发布页 ↗</a>
          </div>
          <div>
            <span>INTEGRATED ROBOT CANDIDATE</span>
            <strong>付费私用 / 未验包</strong>
            <p>JRIZZ / Cults 页面列出 Fusion 360 F3Z、STL、机器人端与遥控端 Arduino 草图；页面称可动但仍在开发。购买和接受 CULTS Private Use 必须等待用户明确确认。</p>
            <a className="inline-download" href="https://cults3d.com/en/3d-model/gadget/d-o-droid-star-wars-droid" target="_blank" rel="noreferrer">查看付费原页 ↗</a>
          </div>
          <div>
            <span>STATIC / ARTICULATED REFERENCES</span>
            <strong>不能替代驱动包</strong>
            <p>WF3D 约300 mm、32文件模型为 CC BY-NC-SA 4.0 静态展示件；Home Decor 是 CC BY-NC 4.0 的11文件WIP remix；Gambody有116个STL和518 mm关节版，但没有控制源码或完整电气设计。</p>
            <a className="inline-download" href="https://www.printables.com/model/147063-star-wars-d-o-droid" target="_blank" rel="noreferrer">WF3D 静态模型 ↗</a>
            <a className="inline-download" href="https://www.printables.com/model/1269542-d-o-droid-star-wars-home-decor" target="_blank" rel="noreferrer">Home Decor WIP ↗</a>
            <a className="inline-download" href="https://www.gambody.com/premium/d-o-droid" target="_blank" rel="noreferrer">Gambody 关节版 ↗</a>
          </div>
          <div>
            <span>CONTROL CODE</span>
            <strong>D22–D25 安全变体已编译</strong>
            <p>v3.4.3 固定到 e90aacd；转换器只接受原始 SHA-256 6cb3ce0d，把四路舵机从 D0/D1/D5/D6 改到 D22–D25，释放 Serial0。Mega 2560 真编译通过：Flash 17%，RAM 18%；修改后源码哈希 f858c485。实体连续性仍为 NOT_RUN，变体源码和二进制未在网站再分发。官网泛名v3.4 ZIP实际仍是v3.4.0，只作历史参考。</p>
            <a className="inline-download" href={asset("/downloads/do_safe_pin_variant_compile.json")} download>下载安全变体编译证据 ↓</a>
            <a className="inline-download" href={asset("/downloads/do_safe_pin_variant_wiring.csv")} download>下载D22–D25线束合同 ↓</a>
            <a className="inline-download" href={asset("/downloads/build_do_safe_pin_variant.py")} download>下载固定哈希转换器 ↓</a>
          </div>
          <div>
            <span>ASSEMBLY</span>
            <strong>免费</strong>
            <p>官网12个附件已在本机逐项校验哈希；公开仓库含5个 Arduino 草图，但整机机械 CAD/STL 为0。AIO32附件22个源码文件已用ESP32 core 3.3.7实编译通过：Flash 41%、RAM 15%，并发现手册遗漏SensorLib依赖；包级LICENSE与KiCad/Gerber仍缺失。60 mm无轮调试支架许可也未明确，均未在网站镜像。</p>
          </div>
          <div>
            <span>MANTIS HACKS</span>
            <strong>参考</strong>
            <p>5集编号构建记录加1个轮胎打印视频；六条公开描述未见 Matt 改版 CAD/程序下载。</p>
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
              href={asset("/downloads/do_aio32_firmware_compile.json")}
              download
            >
              下载AIO32实编译证据 ↓
            </a>
            <a
              className="inline-download"
              href={asset("/downloads/do_mantis_video_audit.json")}
              download
            >
              下载Mantis视频描述审计 ↓
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
              下载26项采购门控BOM ↓
            </a>
          </div>
        </div>
      </section>

      <section className="section build" id="build">
        <div className="section-head">
          <span>05 / EXECUTABLE ASSEMBLY</span>
          <h2>24 个装配步骤 + 19 个真机门，从模型到可控机器</h2>
          <p>装配进度保存在本机浏览器。每一步均给出零件、工具、动作与验收门槛；最终能否运行由阶段16真实证据矩阵决定，实物尺寸和安全限值仍须用采购件复测。</p>
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
          <br />
          GitHub：<a href={repositoryUrl} target="_blank" rel="noreferrer">{repositoryUrl}</a>
        </p>
        <b>REP·LAB / BUILD LOG 001</b>
      </footer>
    </main>
  );
}
