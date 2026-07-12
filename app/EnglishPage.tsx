"use client";

import { useEffect, useRef, useState } from "react";
import { assemblyStepsEn } from "./data/assemblyStepsEn";

const asset = (path: string) => `${import.meta.env.BASE_URL}${path.replace(/^\/+/, "")}`;

const views = [
  { label: "Front", src: asset("/model/bb8-front.png") },
  { label: "Side", src: asset("/model/bb8-side.png") },
  { label: "Rear", src: asset("/model/bb8-back.png") },
];

type AssemblyMedia = { label: string; src: string; alt: string; note: string };

const phaseMedia: Record<string, AssemblyMedia[]> = {
  "Reference & fabrication": [
    { label: "Front", src: asset("/model/bb8-front.png"), alt: "BB-8 1:1 front reference", note: "Lock the head/body silhouette, eye position and print scale." },
    { label: "Side", src: asset("/model/bb8-side.png"), alt: "BB-8 1:1 side reference", note: "Check the head overlap, antennas and spherical panel envelope." },
    { label: "Rear", src: asset("/model/bb8-back.png"), alt: "BB-8 1:1 rear reference", note: "Check service panels, seams and rear-panel direction." },
  ],
  Chassis: [
    { label: "Front", src: asset("/model/internal_front.png"), alt: "BB-8 chassis front view", note: "Check the 310 mm track, wheel contact and low mass placement." },
    { label: "Side", src: asset("/model/internal_side.png"), alt: "BB-8 chassis side view", note: "Check drive axes, ballast height and shell clearance." },
    { label: "Top", src: asset("/model/internal_top.png"), alt: "BB-8 chassis top view", note: "Check motors, rails, harnesses and the equator service zone." },
  ],
  "Electrical & ballast": [
    { label: "Side", src: asset("/model/internal_side.png"), alt: "BB-8 internal side view", note: "Check the sealed ballast cassette, battery, electronics and harness bend radii." },
    { label: "Top", src: asset("/model/internal_top.png"), alt: "BB-8 internal top view", note: "Check power/signal separation and access to all four service connectors." },
  ],
  "Magnetic head": [
    { label: "Mechanism", src: asset("/model/bb8-mechanism.png"), alt: "BB-8 magnetic head mechanism", note: "Check the 6+6 magnet arrays, 8 mm gap and three follower rollers." },
    { label: "Side", src: asset("/model/internal_side.png"), alt: "BB-8 mast and head side view", note: "Check mast, top carrier and head rolling envelope." },
  ],
  "Close the shell": [
    { label: "Side", src: asset("/model/bb8-side.png"), alt: "BB-8 closed-shell side view", note: "After closing the equator, check head clearance, seams and rolling envelope." },
    { label: "Rear", src: asset("/model/bb8-back.png"), alt: "BB-8 closed-shell rear view", note: "Recheck rear details, equator step and service orientation." },
  ],
  "Flash & calibrate": [
    { label: "Three views", src: asset("/model/BB8_internal_three_view.png"), alt: "BB-8 internal three-view sheet", note: "Before raised-wheel calibration, verify wheel direction, IMU axes, E-stop and connectors." },
    { label: "Mechanism", src: asset("/model/bb8-mechanism.png"), alt: "BB-8 mechanism check", note: "Before floor testing, recheck magnetic coupling, wheel contact and safety clearances." },
  ],
};

const sources = [
  { name: "StarWars.com production interview", tag: "official production facts", href: "https://www.starwars.com/news/droid-dreams-how-neal-scanlan-and-the-star-wars-the-force-awakens-team-brought-bb-8-to-life" },
  { name: "StarWars.com BB-8 databank", tag: "official 0.67 m height", href: "https://www.starwars.com/databank/bb-8/" },
  { name: "Photographic BB-8 dimensions", tag: "community measurement", href: "https://rimstar.org/science_electronics_projects/bb-8_dimensions.htm" },
  { name: "BB-8 Builders Club V3.1 orientation guide", tag: "CC BY-NC-SA 4.0", href: "https://bb8builders.club/wiki/images/6/68/BB-8-V3-Panel-Orientation-Guide.pdf" },
  { name: "James Bruton BB-8 v2 CAD/code", tag: "licence needs review", href: "https://github.com/XRobots/BB82_public" },
  { name: "Printed Droid D-O knowledge base", tag: "public documentation", href: "https://www.printed-droid.com/kb/d-o/" },
  { name: "D-O assembly manual", tag: "free to read", href: "https://d-o.dozuki.com/c/D-O_Assembly" },
  { name: "D-O control software", tag: "personal non-commercial", href: "https://github.com/PrintedDroid/D-O-Printed-Droid" },
  { name: "Mantis Hacks D-O series", tag: "video / BOM", href: "https://youtube.com/playlist?list=PLTSAQ5KEjPVCldgA1t-KT1lRTKJdAY7er" },
  { name: "Mr Baddeley D-O V2", tag: "paid Patreon files", href: "https://www.patreon.com/mrbaddeley" },
];

export default function EnglishPage() {
  const [view, setView] = useState(0);
  const [step, setStep] = useState(0);
  const [completed, setCompleted] = useState<string[]>([]);
  const [assemblyZoom, setAssemblyZoom] = useState(100);
  const [assemblyView, setAssemblyView] = useState(0);
  const mediaDialog = useRef<HTMLDialogElement>(null);

  useEffect(() => {
    const saved = Number(window.localStorage.getItem("bb8-assembly-step-en"));
    if (Number.isInteger(saved) && saved >= 0 && saved < assemblyStepsEn.length) window.queueMicrotask(() => setStep(saved));
  }, []);
  useEffect(() => window.localStorage.setItem("bb8-assembly-step-en", String(step)), [step]);
  useEffect(() => {
    try {
      const saved = JSON.parse(window.localStorage.getItem("bb8-completed-steps-en") ?? "[]");
      if (Array.isArray(saved)) window.queueMicrotask(() => setCompleted(saved.filter((id) => typeof id === "string")));
    } catch { /* Ignore invalid local progress. */ }
  }, []);
  useEffect(() => window.localStorage.setItem("bb8-completed-steps-en", JSON.stringify(completed)), [completed]);

  const activeStep = assemblyStepsEn[step];
  const mediaOptions = phaseMedia[activeStep.phase];
  const activeMedia = mediaOptions[assemblyView] ?? mediaOptions[0];
  const isCompleted = completed.includes(activeStep.id);
  const changeStep = (next: number) => { setStep(next); setAssemblyView(0); setAssemblyZoom(100); };
  const toggleCompleted = () => setCompleted((current) => isCompleted ? current.filter((id) => id !== activeStep.id) : [...current, activeStep.id]);

  return (
    <main>
      <nav className="nav">
        <a className="brand" href="#top"><span>R</span>EP·LAB</a>
        <div>
          <a href="#model">BB-8</a><a href="#do">D-O</a><a href="#build">Build</a><a href="#sources">Sources</a>
          <a className="language-link" href={asset("")} aria-label="Switch to Chinese">中文</a>
        </div>
      </nav>

      <section className="hero" id="top">
        <div className="eyebrow">SCREEN-REFERENCED · 1:1 BUILD</div>
        <h1>Turn the screen droid<br /><em>into a real machine.</em></h1>
        <p>A maker-focused BB-8 parametric model, auditable D-O resource map and safety-gated assembly guide. Facts, assumptions, paid files and licence boundaries remain explicit.</p>
        <div className="hero-actions"><a className="button primary" href="#model">View model evidence</a><a className="button" href="#build">Start the build ↓</a></div>
        <div className="metrics">
          <div><b>508</b><span>mm body diameter</span></div><div><b>295</b><span>mm head diameter</span></div><div><b>670</b><span>mm antenna-free height</span></div>
        </div>
      </section>

      <section className="section model-section" id="model">
        <div className="section-head">
          <span>01 / BB-8 DIGITAL TWIN</span><h2>One editable 1:1 model,<br />three orthographic views</h2>
          <p>The official databank gives 0.67 m character height. The 508 mm sphere and 295 mm head come from photographic measurement and full-size community builds—not Lucasfilm CAD. Antennas remain calibration parameters.</p>
        </div>
        <div className="viewer">
          <div className="tabs">{views.map((item, index) => <button key={item.label} className={view === index ? "active" : ""} onClick={() => setView(index)}>{item.label}</button>)}</div>
          <img src={views[view].src} alt={`BB-8 ${views[view].label} view`} /><div className="scale"><span>0</span><i></i><span>508 mm</span></div>
        </div>
      </section>

      <section className="section structure">
        <div className="section-head"><span>02 / BUILDABLE ARCHITECTURE</span><h2>A replica architecture you can assemble</h2></div>
        <div className="cards">
          <article><b>A</b><h3>Shell and panels</h3><p>Two 20-inch-class shell halves with separate appearance panels, service openings and wear surfaces.</p></article>
          <article><b>B</b><h3>Low-CoM chassis</h3><p>Differential drive, low battery and sealed ballast placement, IMU control and fail-safe stopping.</p></article>
          <article><b>C</b><h3>Magnetic head</h3><p>Top-mounted internal magnets and follower rollers. This is a community replica architecture, not disclosed film-unit engineering.</p></article>
        </div>
        <div className="mechanism">
          <img src={asset("/model/BB8_internal_three_view.png")} alt="BB-8 internal mechanism front side and top views" />
          <div><span className="kicker">BUILDABLE CORE / STAGE 15</span><h3>Editable parts,<br />not a concept image.</h3>
            <p>The Blender master now contains 147 fabrication objects plus three non-fabrication engineering markers. Wheels and four stabilisers reach the 254 mm inner shell; IG42E-24K envelopes use 125.2 mm length, 35 mm PCD mounts and 310 mm track. Stage 14 adds the removable 1.50 kg sealed ballast cassette. Stage 15 adds explicit left/right motor-driver envelopes, heatsinks, main fuse, normally-open contactor, dual-channel normally-closed E-stop, safety relay, service disconnect and tether jack. Product ratings remain unfrozen and all live hardware tests remain NOT_RUN.</p>
            <div className="doc-actions">
              <a className="button" href={asset("/downloads/BB8_BOM.md")} download>BB-8 BOM</a>
              <a className="button" href={asset("/downloads/internal_assembly_manifest.csv")} download>147-part manifest</a>
              <a className="button" href={asset("/downloads/BB8_stage14_mass_cg_inertia_validation.md")} download>Stage 14 mass report</a>
              <a className="button" href={asset("/downloads/BB8_stage15_drive_power_dynamic_stability.md")} download>Stage 15 drive/stability report</a>
              <a className="button" href={asset("/downloads/mass_properties_input.json")} download>Mass assumptions</a>
              <a className="button" href={asset("/downloads/mass_properties_results.json")} download>Verified results</a>
              <a className="button" href={asset("/model/BB8_three_view_dimension_sheet.png")} download>Dimension sheet</a>
            </div>
          </div>
        </div>
        <div className="motion-lab">
          <div><span className="kicker">KINEMATIC PROOF / 120 FRAMES</span><h3>The sphere rolls.<br />The chassis does not tumble.</h3>
            <p>The animation locks <code>s = Rθ</code>: one body revolution travels 1.595929 m and the 96 mm drive wheels turn 5.291667 revolutions. Chassis pitch illustrates acceleration/braking while the head target remains world-vertical.</p>
            <div className="download-grid"><a href={asset("/model/BB8_1to1_kinematic.glb")} download>Animated GLB</a><a href={asset("/model/BB8_internal_mechanism_mm.stl")} download>Internal STL</a><a href={asset("/downloads/BB8_kinematics.md")} download>Kinematics report</a><a href={asset("/downloads/kinematics.csv")} download>120-frame data</a></div>
          </div>
          <video controls autoPlay loop muted playsInline poster={asset("/model/bb8-front.png")}><source src={asset("/model/BB8_kinematic_cycle.mp4")} type="video/mp4" /></video>
        </div>
      </section>

      <section className="section firmware-section" id="control">
        <div className="section-head"><span>03 / MOTION CONTROLLER</span><h2>It must move—<br />and it must stop.</h2><p>The C++ core and ESP32-S3 adapter compile with quadrature encoders, MPU6050 and dual INA226 current sensing. Stage 15 turns the fuse, normally-open contactor, dual-channel E-stop and both driver-enable branches into an explicit physical contract. Product selection, wiring, thresholds and powered bench tests remain NOT_RUN.</p></div>
        <div className="control-grid">
          <article><span>01</span><h3>200 Hz closed loop</h3><p>Wheel-speed PI plus IMU yaw-rate correction; straight-run RMS error is 0.00772 m/s.</p></article>
          <article><span>02</span><h3>11 latched faults</h3><p>Stale sensors, hardware ALERT, overcurrent and persistent stall all remove PWM and EN in the same frame.</p></article>
          <article><span>03</span><h3>91.20° dynamic turn</h3><p>The closed-loop scenario includes inertia, rolling resistance, encoder quantisation and battery sag.</p></article>
          <article><span>04</span><h3>Failure while moving</h3><p>After a 0.20 m/s restart, injected stale IMU data zeros PWM immediately; speed is 0.00224 m/s after 0.8 s.</p></article>
          <article><span>05</span><h3>Fail-closed sensors</h3><p>Encoder CPR defaults to zero; EN stays off until 400 stationary MPU6050 samples complete.</p></article>
          <article><span>06</span><h3>Hard de-energising E-stop</h3><p>Two normally-closed channels drive the safety relay and normally-open contactor. First tests require a wired tether; wireless alone is not accepted.</p></article>
        </div>
        <div className="firmware-downloads"><a href={asset("/downloads/BB8_controller_core.zip")} download>C++ control core</a><a href={asset("/downloads/BB8_ESP32_S3_firmware.zip")} download>ESP32-S3 draft</a><a href={asset("/downloads/BB8_closed_loop_simulation.md")} download>Closed-loop evidence</a><a href={asset("/downloads/BB8_stage12_power_safety.md")} download>Power-safety report</a><a href={asset("/downloads/BB8_stage13_power_hardware.md")} download>Protection hardware model</a></div>
      </section>

      <section className="section firmware-section" id="physics">
        <div className="section-head"><span>04 / MASS, COM & PHYSICS GATE</span><h2>Calculate first.<br />Then test on the floor.</h2><p>Stage 14 replaces the unverified 110 mm CoM claim with a 17-group mass ledger. Stage 15 adds grade gravity, shell inertia, wheel/shell traction, differential turning, resultant lean and head shock to one rerunnable envelope. PASS applies only to traceable assumptions, never to physical hardware.</p></div>
        <div className="control-grid">
          <article><span>01</span><h3>8.463 kg nominal</h3><p>Assumption range is 6.375–10.628 kg. Every mass group remains NOT_RUN until weighed.</p></article>
          <article><span>02</span><h3>56.2 mm nominal CoM</h3><p>Nominal z=-56.2 mm; the worst enumerated corner still gives z=-27.7 mm.</p></article>
          <article><span>03</span><h3>3° dynamic grade point</h3><p>At 0.20 m/s², 0.30 m/s and a 0.80 m turn radius, each motor needs 0.289 N·m.</p></article>
          <article><span>04</span><h3>2.07× torque margin</h3><p>The 3° point just clears the 2× gate. The zero-acceleration analytical grade ceiling is about 4.50°, not a physical rating.</p></article>
          <article><span>05</span><h3>4.22° resultant lean</h3><p>Grade, longitudinal acceleration and turn acceleration combine below the 12° design contract.</p></article>
          <article><span>06</span><h3>No unpowered slope hold</h3><p>There is no mechanical parking brake, so the sphere cannot hold position on a grade after power removal.</p></article>
        </div>
        <div className="firmware-downloads"><a href={asset("/downloads/BB8_stage14_mass_cg_inertia_validation.md")} download>English Stage 14 report</a><a href={asset("/downloads/BB8_stage15_drive_power_dynamic_stability.md")} download>English Stage 15 report</a><a href={asset("/downloads/BB8_阶段15_驱动电源与动态稳定性.md")} download>Chinese Stage 15 report</a><a href={asset("/downloads/stability_envelope_input.json")} download>Stability inputs</a><a href={asset("/downloads/stability_envelope_results.json")} download>Stability results</a><a href={asset("/downloads/stability_envelope_sweep.csv")} download>Grade/acceleration sweep</a><a href={asset("/downloads/mass_properties_scenarios.csv")} download>Mass scenarios CSV</a></div>
      </section>

      <section className="section do-section" id="do">
        <div className="do-copy"><span className="kicker">D-O / RESOURCE MAP</span><h2>Open source is not<br />the same as visible online.</h2><p>No freely redistributable complete D-O mechanical package was found. Public assembly/wiring/BOM material plus personal non-commercial control source can still form an auditable self-build route. The 24-line procurement gate and D01–D16 commissioning path hold purchases where MDD10A versus dual MD10C, motor/servo loads or power protection are unresolved.</p></div>
        <div className="do-grid">
          <div><span>MECHANICAL CAD</span><strong>Paid</strong><p>Mr Baddeley D-O V2 STL/Fusion files are Patreon member resources and are not mirrored here.</p></div>
          <div><span>CONTROL CODE</span><strong>Version pinned</strong><p>Printed Droid v3.4.3 is pinned to e90aacd. Its README allows personal non-commercial use, modification and distribution with notice and attribution. Mega 2560 compilation passes at 17% flash and 18% RAM.</p></div>
          <div><span>ASSEMBLY</span><strong>Free to read</strong><p>Two Printed Droid PDFs are hash-verified. The public repository contains five Arduino sketches and zero complete mechanical CAD/STL files.</p></div>
          <div><span>MANTIS HACKS</span><strong>Reference</strong><p>The six-part build log and BOM are useful evidence; no downloadable Matt-modified CAD or program was located.</p><a className="inline-download" href={asset("/downloads/DO_resources.md")} download>Resource index ↓</a><a className="inline-download" href={asset("/downloads/DO_resource_audit.md")} download>Licence audit ↓</a><a className="inline-download" href={asset("/downloads/DO_self_build_route.md")} download>D01–D16 route ↓</a><a className="inline-download" href={asset("/downloads/do_self_build_bom.csv")} download>24-line gated BOM ↓</a></div>
        </div>
      </section>

      <section className="section build" id="build">
        <div className="section-head"><span>05 / EXECUTABLE ASSEMBLY</span><h2>24 acceptance-gated steps, from model to controlled machine</h2><p>Progress is stored only in this browser. Every step specifies parts, tools, action and acceptance; purchased-part dimensions and safety limits must still be re-measured.</p></div>
        <div className="progress-summary" aria-label="Assembly progress"><div><span>Current position</span><b>{step + 1} / {assemblyStepsEn.length}</b></div><div><span>Actually complete</span><b>{completed.length} / {assemblyStepsEn.length}</b></div></div>
        <div className="progress position-progress"><i style={{ width: `${((step + 1) / assemblyStepsEn.length) * 100}%` }}></i></div><div className="progress completion-progress"><i style={{ width: `${(completed.length / assemblyStepsEn.length) * 100}%` }}></i></div>
        <div className="assembly-phases" aria-label="Assembly phase navigation">{Object.keys(phaseMedia).map((phase) => { const first = assemblyStepsEn.findIndex((item) => item.phase === phase); const phaseSteps = assemblyStepsEn.filter((item) => item.phase === phase); const count = phaseSteps.filter((item) => completed.includes(item.id)).length; return <button key={phase} className={activeStep.phase === phase ? "active" : ""} onClick={() => changeStep(first)}>{phase}<small>{count}/{phaseSteps.length}</small></button>; })}</div>
        <div className="assembly-media"><div className="assembly-media-frame"><img src={activeMedia.src} alt={activeMedia.alt} style={{ transform: `scale(${assemblyZoom / 100})` }} /></div><div className="assembly-media-controls"><b>{activeStep.phase} · {activeMedia.label}</b><p>{activeMedia.note}</p><div className="assembly-view-tabs">{mediaOptions.map((media, index) => <button key={media.label} type="button" className={assemblyView === index ? "active" : ""} onClick={() => setAssemblyView(index)}>{media.label}</button>)}</div><label htmlFor="assembly-zoom-en">View zoom: {assemblyZoom}%</label><input id="assembly-zoom-en" type="range" min="80" max="180" value={assemblyZoom} onChange={(event) => setAssemblyZoom(Number(event.target.value))} /><div className="assembly-media-actions"><button type="button" onClick={() => setAssemblyZoom(100)}>Reset view</button><button type="button" onClick={() => mediaDialog.current?.showModal()}>Open large image</button></div></div></div>
        <dialog className="assembly-dialog" ref={mediaDialog}><button type="button" aria-label="Close large image" onClick={() => mediaDialog.current?.close()}>Close ×</button><img src={activeMedia.src} alt={activeMedia.alt} /><p>{activeMedia.note}</p></dialog>
        <div className="step-card"><div className="step-no">{String(step + 1).padStart(2, "0")}</div><div><small>{activeStep.phase} · {activeStep.id} · STEP {step + 1} OF {assemblyStepsEn.length}</small><h3>{activeStep.title}</h3><dl className="step-detail"><div><dt>Parts</dt><dd>{activeStep.parts}</dd></div><div><dt>Tools</dt><dd>{activeStep.tools}</dd></div><div><dt>Action</dt><dd>{activeStep.action}</dd></div><div><dt>Accept</dt><dd>{activeStep.acceptance}</dd></div></dl>{activeStep.warning && <p className="step-warning">Safety: {activeStep.warning}</p>}<button type="button" className={`step-complete ${isCompleted ? "done" : ""}`} onClick={toggleCompleted}>{isCompleted ? "✓ Step complete" : "Mark step complete"}</button><div className="step-nav"><button disabled={step === 0} onClick={() => changeStep(step - 1)}>← Previous</button><button disabled={step === assemblyStepsEn.length - 1} onClick={() => changeStep(step + 1)}>Next →</button></div></div></div>
      </section>

      <section className="section sources" id="sources"><div className="section-head"><span>06 / SOURCES & LICENCES</span><h2>What you may use,<br />and where the boundary is</h2></div><div className="source-list">{sources.map((source, index) => <a href={source.href} target="_blank" rel="noreferrer" key={source.name}><span>{String(index + 1).padStart(2, "0")}</span><b>{source.name}</b><em>{source.tag}</em><i>↗</i></a>)}</div></section>
      <footer><p>Unofficial fan research and personal educational prototype. STAR WARS, BB-8, D-O and related characters belong to their respective rights holders. Check each licence before printing, modifying or redistributing files.</p><b>REP·LAB / BUILD LOG 001</b></footer>
    </main>
  );
}
