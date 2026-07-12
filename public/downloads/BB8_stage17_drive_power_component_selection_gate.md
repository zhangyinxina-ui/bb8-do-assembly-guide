# BB-8 Stage 17: drive-power component selection gate

> Result: **HOLD_COMPONENT_FREEZE_MEASUREMENTS_REQUIRED**. All 15 official-data-sheet rating screens pass, but this is neither purchase release nor physical validation. Motor stall current, MDD20A regeneration and hard-disable adaptation, fuse I²t, exact contactor ordering/suppression, a compact 4S BMS, professional pack design and all nineteen commissioning gates remain open.

## Deliverables

- `engineering/power_component_candidates.json` separates official ratings, calculations and unknowns.
- `tools/verify_power_component_selection.py` recalculates margins and refuses to treat unresolved items as frozen.
- `engineering/power_component_selection_results.json` is the current machine-readable HOLD result.
- `tests/test_power_component_selection.py` covers the honest HOLD, an undersized driver and the contactor suppression timing boundary.

No purchase, pack fabrication, powered test, stall test or floor run occurred. The Blender master was not changed and no new `.blend` copy was created.

## Candidate matrix

| Module | Candidate | Official rating screen | Current state |
|---|---|---|---|
| Motor | Sha Yang Ye / Cytron IG42E-24K | 12 V, 5.5 A rated, 0.98 N·m, 248 rpm | `HOLD_MEASURE_STALL_CURRENT`; the official page does not publish stall current |
| Dual driver | Cytron MDD20A | 6–30 V; 20 A continuous/60 A peak per channel; 3.3 V PWM/DIR compatible | `HOLD_INTERFACE_AND_REGEN` |
| Main fuse | provisional Littelfuse 498 MIDI 30 A | 32 VDC; typical 2.06 mΩ for the 30 A part | `HOLD_STALL_I2T_CABLE_AND_TEMPERATURE` |
| Main contactor | Albright SW60 SPST-NO with auxiliary contact required | 80 A thermal; 120 A resistive breaking at 48 V | `HOLD_ORDER_CODE_SUPPRESSION_AND_DROP_TEST` |
| Cell/pack | Molicel P28A, professionally built 4S2P candidate | 14.4 V nominal/16.8 V charge; theoretical 70 A discharge | `HOLD_BMS_PACK_SHOP_AND_THERMAL_TEST` |
| BMS | not frozen | 4S, at least 30 A discharge, 10 A regenerative charge, two temperatures and a documented regeneration path | `HOLD_NO_COMPACT_OFFICIAL_4S_CANDIDATE_FROZEN` |

## Analytical margins

Using the Stage-15 total analytical peak of 21 A and the 5.5 A motor rating:

- MDD20A continuous current is **3.64×** motor rated current per channel; its stated peak is **5.71×** the 10.5 A analytical peak per channel; its 30 V limit is **1.79×** the 16.8 V bus maximum.
- The provisional 30 A MIDI fuse is **1.43×** the 21 A analytical peak and its 32 V rating is **1.90×** bus maximum. Stall waveform, harness temperature and I²t coordination can still change the fuse.
- SW60 thermal current is **3.81×** the analytical peak; its 120 A resistive breaking figure at 48 V is **5.71×** that peak.
- A theoretical P28A 4S2P pack provides **3.33×** the analytical peak. Topology-based DC resistance is about 40 mΩ, close to the earlier 50 mΩ analytical assumption.

These figures are catalogue screening only. MDD20A's 60 A peak is a temperature-dependent current limit and the official data sheet does not specify a duration.

## Two interface blockers

### No independent MDD20A enable input

The official interface is dual PWM+DIR, and PWM-low is documented as `Brake`, not electrical isolation. The upstream contactor must therefore remove drive-bus power, and the existing left/right EN contract needs a separately designed and tested dual-channel hardware gate. PWM zero, lost MCU commands and software latches must not be described as hard de-energisation.

### Regenerative path is not frozen

The selected official MDD20A sources do not state regenerative-energy handling for this application. Stage-16 gate P01 must still capture bus peaks during controlled deceleration and E-stop, then prove that driver, BMS and cell charge limits are respected.

## Contactor suppression timing

The SW60 data sheet gives typical release times of 6 ms without suppression, 35 ms with a diode, and 8–20 ms with a diode plus resistor. The system contract is at most 20 ms. A plain flyback diode therefore fails the catalogue-level timing screen. The final clamp must be checked for device ratings and EMC, then measured on the actual coil and bus; this report deliberately does not provide a copy-paste resistor value.

## Geometry boundary

The official MDD20A drawing gives an approximately **88.90 × 78.74 mm** board, **83.82 × 73.66 mm** hole spacing and four Ø3 mm holes. This is substantially larger than the two 52 × 34 × 16 mm generic envelopes currently in Blender, and the official drawing does not freeze height. With BMS, harness and packaging still unresolved, Stage 17 does not force an unverified catalogue envelope into the sole master `.blend`.

## Battery-pack boundary

The P28A sheet states 4.2 V charge, 35 A maximum discharge and 8.4 A maximum charge per cell. It does not authorise hand-built packs from this report. A qualified pack builder must release cell matching, interconnects, insulation, fusing, thermistors, venting, enclosure, connectors, BMS, charger and transport compliance.

The EMUS BMS mini was checked as an official-data reference and rejected because its manual specifies five to sixteen cells. No loose cells should be purchased for pack construction until a suitable 4S BMS and professional pack design are frozen.

## Gates before purchase release

1. Measure startup and controlled-stall current on both actual IG42E motors in a current-limited, wheels-up fixture.
2. Design and bench-test the external dual-channel MDD20A safety gate; E-stop must remove both contactor and control paths.
3. Capture regenerative bus waveforms during deceleration and E-stop.
4. Coordinate fuse I²t and harness temperature against measured waveforms.
5. Freeze the exact non-latching SW60 12 V continuous-coil, auxiliary-contact and suppression configuration; measure release at no more than 20 ms.
6. Freeze a documented 4S BMS and professionally released pack.
7. Pass all nineteen Stage-16 physical evidence gates before removing the system run HOLD.

## Official sources

- Cytron MDD20A: <https://www.cytron.io/p-20amp-6v-30v-dc-motor-driver-2-channels>
- Cytron IG42E-24K: <https://www.cytron.io/p-12v-248rpm-10kgfcm-planetary-dc-geared-motor-with-encoder>
- Littelfuse MIDI 32 V data sheet: <https://www.littelfuse.com/~/media/automotive/datasheets/fuses/passenger-car-and-commercial-vehicle/bolt-down-fuses/littelfuse_midi_datasheet.pdf>
- Albright SW60 data sheet: <https://www.albrightinternational.com/wpcms/wp-content/uploads/2020/08/SW60-Data-Sheet.pdf>
- Molicel INR-18650-P28A data sheet: <https://www.molicel.com/wp-content/uploads/INR18650P28A-V2-80093.pdf>
- EMUS BMS mini manual: <https://emusbms.com/wp-content/uploads/2019/05/EMUS-BMS-mini-User-Manual-v0.9.pdf>
