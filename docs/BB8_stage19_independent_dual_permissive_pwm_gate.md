# BB-8 Stage 19: Independent dual-permissive PWM gate pre-CAD design gate

> Conclusion: **all 64 Boolean combinations, input-current, logic-level, resistor-derating and 50 x 35 x 15 mm envelope checks pass. There is still no KiCad schematic, ERC/DRC, Gerber, assembled board or oscilloscope evidence, so the result remains `HOLD_PCB_CAD_BENCH_AND_SAFETY_VALIDATION_REQUIRED`.**

## Purpose

Stage 17 established that MDD20A exposes PWM+DIR but no independent enable, and that PWM low is brake rather than electrical isolation. Stage 18 reserved a 50 x 35 x 15 mm gate-board volume without releasing a circuit. Stage 19 turns that placeholder into a machine-auditable pre-CAD reference design while retaining the safety relay and normally-open SW60-class contactor as the actual motor-bus isolation path.

## Three-permissive chain

Both motor channels implement:

`PWM_OUT = LOGIC_POWER_OK AND PWM_IN AND SAFE_A_OK AND SAFE_B_OK AND ALERT_N`

| Stage | Device | Function | Fail-low target |
| --- | --- | --- | --- |
| A/B inputs | 2 x Vishay VO617A-4 | Isolate 12.0–16.8 V energise-to-run loops into 3.3 V permissives | Removing either loop drops its permissive |
| Permissive A | TI SN74LVC2G08 U3 | Gate both PWM inputs with `SAFE_A_OK` | A alone blocks both PWM outputs |
| Permissive B | TI SN74LVC2G08 U4 | Gate both U3 outputs with `SAFE_B_OK` | B alone blocks both PWM outputs |
| Current alert | TI SN74LVC2G08 U5 | Gate both U4 outputs with dual-INA226 open-drain `ALERT_N` | Either hardware ALERT blocks both PWM outputs |
| Bus isolation | Safety relay + NO contactor | Remove the motor bus in parallel with the PWM gate | PWM low never substitutes for this layer |

`DIR_L/R` are direct pass-through signals, not safety signals. The design is therefore valid only for MDD20A sign-magnitude operation.

## Official data and calculations

- [TI SN74LVC2G08 data sheet](https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf): `VIH >= 2.0 V` and `VIL <= 0.8 V` at 3.0–3.6 V; maximum 5.3 ns per gate at 3.3 V ±0.3 V and -40–125 °C; `Ioff` supports partial-power-down protection.
- [Vishay VO617A data sheet](https://www.vishay.com/docs/83430/vo617a.pdf): VO617A-4 CTR is 160–320% at `IF=5 mA`, `VCE=5 V`, 25 °C; maximum `VCE(sat)` is 0.4 V at `IF=5 mA`, `IC=1 mA`. The 25 µs saturated turn-off is typical, not a maximum bound.
- [Cytron MDD20A product page](https://sg.cytron.io/p-20amp-6v-30v-dc-motor-driver-2-channels): inputs accept 1.8/3.3/5/12 V logic and PWM up to 20 kHz.
- [JST XH official catalogue](https://www.jst-mfg.com/product/pdf/eng/eXH.pdf): 2.5 mm pitch; the standard top-entry series has 9.8 mm mounting height and a 3 A rating with AWG22.

At 12.0 V and the data-sheet 1.65 V forward-voltage upper point, the 2.00 kΩ input resistor gives 5.175 mA, reaching the 5 mA CTR test point. At 16.8 V and 1.0 V forward voltage it gives 7.900 mA. Worst resistor dissipation is 0.12482 W, so a 0.5 W part provides 4.006x derating. With the 0.4 V saturation limit, the emitter-follower high model is 2.9 V—above the 2.0 V LVC threshold—and its 4.7 kΩ load is about 0.617 mA, below the 1 mA saturation test current.

The three-package LVC chain has a 15.9 ns digital maximum. The optocoupler switching figure is typical only, so the complete 20 ms de-energise limit still requires oscilloscope evidence.

## Mechanical and manufacturing boundary

- Proposed PCB: 50 x 35 x 1.6 mm, four Ø3.2 mm holes. With the 9.8 mm JST XH envelope, estimated assembled height is 11.4 mm, leaving 3.6 mm inside the Stage-18 keepout.
- The OpenSCAD source contains only board, holes and component envelopes. It has no pads, copper, solder mask, silkscreen, creepage or cable-bend proof. The local OpenSCAD 2021.01 headless export did not complete within the bounded run, so Stage 19 does not claim an STL.
- There is no `.kicad_sch`, `.kicad_pcb`, Gerber or drill release. This stage does not authorise a PCB order.

## Released evidence

- [Machine contract](../engineering/stage19_dual_permissive_gate_contract.json)
- [64-row truth table](../engineering/stage19_gate_truth_table.csv)
- [Provisional BOM](../engineering/stage19_gate_bom.csv)
- [Pin netlist](../engineering/stage19_gate_netlist.csv)
- [Current HOLD result](../engineering/stage19_dual_permissive_gate_results.json)
- [Verifier](../tools/verify_dual_permissive_gate.py)
- [Hardware package notes](../hardware/stage19_dual_permissive_gate/README.md)

## Next non-skippable gates

1. Capture and peer-review the KiCad schematic; pass ERC.
2. Route the PCB, review isolation, mounting, polarity, test points and harness exits; pass DRC.
3. Review Gerber and drill plots before any fabrication order.
4. Measure A/B input current, output levels and temperature at 12.0 V and 16.8 V.
5. Capture A-open, B-open, ALERT-low, 3.3 V-loss and MCU-stuck-high waveforms.
6. Prove both PWM outputs fall within 20 ms, then combine the board, relay and contactor in commissioning test E02.
7. Complete 20 kHz integrity, temperature, vibration, connector-retention and EMC testing.

Physical status: `NOT_RUN`; safety certification: `NONE`; manufacturing release: `NOT_RELEASED_NO_KICAD_GERBER`.
