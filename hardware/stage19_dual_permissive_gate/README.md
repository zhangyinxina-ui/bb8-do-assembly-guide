# Stage 19 dual-permissive PWM gate — routed PCB/DRC reference design

This package replaces the Stage-18 empty gate-board placeholder with a reviewable electrical contract, deterministic KiCad 10 schematic and a real 50 × 35 mm two-layer routed PCB. KiCad 10.0.4 reports **0 ERC violations, 0 PCB DRC violations and 0 unconnected items**. The 34 electrical references, 91 pin assignments and 21 named nets match the canonical CSV; the PCB adds four contracted 3.2 mm M3 NPTH mounting holes. It is deliberately **not a fabrication release**: independent schematic/layout peer review, intentional Gerber/drill review, fabrication, continuity, power-up and bench waveforms remain absent.

## Intended function

```mermaid
flowchart LR
  MCU[MCU PWM L/R] --> A[U3: AND SAFE_A_OK]
  A --> B[U4: AND SAFE_B_OK]
  B --> C[U5: AND ALERT_N]
  C --> MDD[MDD20A PWM L/R]
  SA[12–16.8 V permissive A] --> OA[VO617A-4 A]
  SB[12–16.8 V permissive B] --> OB[VO617A-4 B]
  OA --> A
  OB --> B
  INA[Dual INA226 open-drain ALERT] --> C
  REL[Safety relay] --> SA
  REL --> SB
  REL --> SW60[Normally-open main contactor]
```

Both outputs follow:

`PWM_OUT = LOGIC_POWER_OK AND PWM_IN AND SAFE_A_OK AND SAFE_B_OK AND ALERT_N`

Either safety channel, a current ALERT, or loss of 3.3 V forces both PWM outputs low. `DIR_L` and `DIR_R` pass through directly and are not safety signals. The contract therefore requires MDD20A sign-magnitude mode, where PWM low is brake.

The board provides six declared test points: `SAFE_A_OK`, `SAFE_B_OK`, `ALERT_N`, `PWM_L_OUT`, `PWM_R_OUT` and `GND`. The PCB-plus-component envelope is 11.4 mm; including the 3.0 mm insulated mounting stack gives 14.4 mm installed height and only 0.6 mm analytical margin inside the Stage-18 keepout.

## Safety boundary

- PWM low is braking, not energy isolation. The independent safety relay and normally-open contactor must still remove the motor bus.
- This is not a safety PLC, certified safety relay or redundant safety controller. Shared power, PCB, connectors, logic packages and the motor driver remain common-cause paths.
- The VO617A-4 CTR and saturation checks in this repository use the manufacturer's 25 °C test points. Its saturated 25 µs turn-off is a typical value, not a guaranteed maximum.
- An open `ALERT_N` wire can be pulled high by R13; that path is not fail-safe. Commissioning must test the sensor harness and MCU freshness latch separately.
- Do not fabricate or energise from these files. The formal schematic, routed layout and DRC are complete as a digital reference, but an independent peer review and intentional Gerber/drill release must happen before any manufacturer order or Stage-E02 bench test.

## Files

- `engineering/stage19_dual_permissive_gate_contract.json` — source-of-truth requirements and official references.
- `engineering/stage19_gate_netlist.csv` — pin-level connectivity contract.
- `engineering/stage19_gate_bom.csv` — provisional BOM; many passives remain manufacturer-TBD.
- `engineering/stage19_gate_truth_table.csv` — all 64 input combinations.
- `engineering/stage19_dual_permissive_gate_results.json` — analytical result and unresolved release gates.
- `stage19_dual_permissive_gate.kicad_sch` / `.kicad_pro` / `.kicad_pcb` — formal KiCad 10 schematic and routed two-layer PCB project.
- `stage19_symbols.kicad_sym` — project-local custom MCU-header and VO617A-4 symbols used by the deterministic capture.
- `engineering/stage19_kicad_erc.json` — KiCad 10.0.4 ERC export with zero violations.
- `engineering/stage19_kicad_netlist.xml` / `stage19_kicad_bom.csv` — machine-audited connectivity and KiCad BOM exports.
- `engineering/stage19_kicad_pcb_drc.json` — KiCad 10.0.4 PCB DRC report with zero violations and zero unconnected items.
- `engineering/stage19_kicad_pcb_verification.json` — structural regeneration, board envelope, mounting-hole, net and DRC evidence.
- `output/pcb/BB8_stage19_gate_pcb_*` — top/bottom copper review plots and a visually inspected isometric render; review images only, not Gerbers.
- `output/pdf/BB8_stage19_dual_permissive_gate_schematic.pdf` — reviewed one-page A4 schematic rendering.
- `tools/verify_stage19_kicad.py` — regenerates, runs ERC/exports and cross-audits the canonical netlist without granting fabrication release.
- `tools/generate_stage19_kicad_pcb.py` — deterministically places and routes the PCB with real KiCad footprints.
- `tools/verify_stage19_kicad_pcb.py` — regenerates the PCB in a temporary directory, compares UUID-independent structure and runs DRC on both copies.
- `tools/export_stage19_kicad_pcb.py` — exports review SVG/PNG files only; it cannot emit Gerber or drill manufacturing data.
- `tools/verify_dual_permissive_gate.py` — deterministic evaluator.
- `board_envelope.scad` — deterministic component-envelope model source. The local OpenSCAD 2021.01 CLI did not complete a headless export, so no STL is claimed in this stage.

## Required next tests

1. Independent peer review of the captured KiCad schematic and its safety assumptions.
2. Independent PCB placement/routing, creepage, courtyard, connector-polarity and test-point peer review; the automated DRC result alone is not release approval.
3. Intentionally generate and manually review Gerber/drill plots before any manufacturer order; none is published in this reference package.
4. Unpowered continuity and polarity inspection.
5. 12.0 V and 16.8 V corner tests for `SAFE_A` and `SAFE_B` independently.
6. Oscilloscope proof that each safety channel, `ALERT_N`, logic-power loss and MCU stuck-high drive both PWM outputs low within 20 ms.
7. 20 kHz PWM integrity, temperature, vibration, connector retention and EMC checks.
8. Combined safety-relay/contactor/PWM-gate Stage-E02 evidence.
