# BB-8 Stage 18: Modular Drive-Power Cassette Layout Gate

> Current result: **HOLD_PHYSICAL_FIT_AND_INTERFACE_VALIDATION_REQUIRED**. The catalogue-envelope layout is now written into the sole Blender master and passes the audit after reopening. No component has been purchased or physically fitted, powered, thermally tested or commissioned.

## Purpose

Stage 17 screened the catalogue ratings of MDD20A, a provisional 30 A MIDI fuse, SW60 and a P28A 4S2P pack candidate. The Stage-15 Blender master still contained two generic 52 x 34 mm driver envelopes. Stage 18 separates official dimensions from unresolved assumptions, lays out and writes:

- an enclosed REC Active BMS 4S candidate;
- one Cytron MDD20A dual driver;
- an Albright SW60 normally-open contactor;
- a service envelope for the replaceable MIDI fuse;
- the REC BMS external current shunt;
- an independently verified dual-channel MDD20A gate-board keepout;
- the safety relay and dual-channel E-stop receiver.

## 4S BMS candidate

The official REC Active BMS manual states:

- dedicated four-cell operation;
- 111 x 135 x 44 mm enclosed, or 109 x 100 x 38 mm including connector without the enclosure;
- up to two DS18B20 pack-temperature sensors;
- up to 2 A active balancing;
- external low-side shunt measurement with a documented +/-200 A range;
- contactor-control relays, charge-disable output, CAN and RS-485.

It is not an inline 30 A MOSFET protection board. It depends on an external shunt and contactors, which is directionally compatible with the current dual-channel E-stop and SW60 architecture. Chemistry, exact order code, shunt and coil interface still require supplier confirmation.

## Analytical layout

| ID | Module | Orientation | Envelope | Status |
|---|---|---|---|---|
| BMS01 | REC Active BMS 4S | Vertical, chassis left | 44 x 111 x 135 mm | Official enclosed envelope; analytical fit only |
| DRV01 | MDD20A | Vertical, chassis right | board 1.6 x 88.9 x 78.74 mm; 25 mm height keepout | Height is an explicit conservative assumption |
| CON01 | SW60 | Upper rear | 81 x 37 x 28.1 mm | Order code, suppression and cable sweep remain open |
| FUS01 | MIDI fuse | Right of contactor | 60 x 25 x 25 mm service keepout | Catalogue fuse body is 41 x 16 mm; holder needs measurement |
| SHN01 | External BMS shunt | Rear left | 50 x 25 x 15 mm keepout | Part, resistance, pulse rating and Kelvin terminals are open |
| GAT01 | Dual-channel gate | Front right | 50 x 35 x 15 mm keepout | No released PCB exists |

## Machine result

`tools/verify_power_cassette_layout.py` checks shell clearance, candidate-to-candidate separation and avoidance of the battery, motors, drive wheels, ballast, magnetic mast and four stabiliser arms. It also refuses to turn unresolved freeze gates into a physical PASS.

- Eight candidates pass the analytical AABB screen.
- Minimum radial shell clearance: **27.643 mm**.
- Minimum candidate-pair separation: **7.500 mm**.
- Minimum separation from protected internal hardware: **6.000 mm**.
- Twelve physical/interface freeze gates remain unresolved.
- Overall result stays `HOLD_PHYSICAL_FIT_AND_INTERFACE_VALIDATION_REQUIRED`.

This conservative axis-aligned screen does not replace real harness bend, tool access, connector insertion, moving-sweep or sealed-shell thermal verification.

## Blender write and reopen audit

After the user explicitly approved discarding the previous unsaved GUI state, the workflow retained one Blender process and one master project. The overwritten on-disk master SHA-256 is `3b774f3e02c89e15922aac48629a43d4765d37078acad88ccf34f6316827d5c3`.

Completed and verified:

- `blender/stage18_power_cassette_geometry.py` creates the envelopes, mounts, two temperature sensors and fifteen power/safety paths;
- `blender/stage18_apply_power_cassette.py` replaces Stage-15 generic envelopes, rerenders the internal views and saves the sole master;
- `blender/audit_bb8.py` confirms 363 total objects, 159 internal objects, 150 fabrication objects, nine engineering annotations, 39 Stage-18 objects, eight candidate IDs, the official MDD20A hole pattern, dual temperature channels and the NOT_RUN boundary after reopening;
- the 150-row fabrication manifest, internal STL, animated GLB and front/side/top internal views were re-exported; Blender was finally restored to the saved master with no unsaved marker.

The audit proves that the saved file reopens with consistent object structure and analytical contracts. It does not promote catalogue envelopes to a physical-fit or powered-test PASS.

## Remaining gates

1. Measure purchased-sample MDD20A total height, terminal sweeps, BMS mounting interface and MIDI holder.
2. Freeze REC chemistry/order code/shunt/contactor-coil interfaces.
3. Release and bench-test the independent dual-channel gate PCB.
4. Complete all nineteen Stage-16 physical evidence gates.

## Official sources

- REC Active BMS 4S manual: <https://www.rec-bms.com/datasheet/Manual_ActiveBMS_4S_RV.pdf>
- Cytron MDD20A product page: <https://www.cytron.io/p-20amp-6v-30v-dc-motor-driver-2-channels>
- Albright SW60 data sheet: <https://www.albrightinternational.com/wpcms/wp-content/uploads/2020/08/SW60-Data-Sheet.pdf>
- Littelfuse MIDI data sheet: <https://www.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/bolt-down-fuses/littelfuse_midi_datasheet.pdf>
