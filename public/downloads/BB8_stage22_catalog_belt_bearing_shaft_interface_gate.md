# BB-8 Stage 22: Catalog Belt, Dual-Bearing Keyed Shaft and Rail Interface Gate

> **HOLD_SUPPLIER_FITS_TENSION_TORQUE_PROOF_AND_PHYSICAL_INTEGRATION_REQUIRED**. Catalog geometry, bearing life, keyed-shaft strength, positive rail load path and shell-envelope screens pass. Fabrication, Blender integration and physical release remain blocked.

## Correcting the Stage-21 belt candidate

- Gates' 2025 industrial catalog starts its standard 15 mm-wide 5MGT list at 300 mm. The Stage-21 **5M-280-15 / 280 mm / 56-tooth** candidate is not in that stock-length table.
- The replacement is official part **5MGT-300-15**, product 92706002: 300 mm pitch length, 60 teeth and 15 mm width.
- Equal 24T, 5 mm-pitch pulleys have 38.197 mm pitch diameter. A 90 mm center distance gives exactly **300.0 mm** closed pitch length at 1:1.
- Twenty-four teeth exceed Gates' 18-tooth 5MGT minimum recommendation. The motor mount provides 4.0 mm total adjustment, exceeding the catalog's 1 mm tensioning allowance.
- Do not force the belt over two flanges. Remove the guard and outboard wheel pulley, then install the belt together with that pulley. Gates DesignFlex or supplier power and installation-tension calculations remain mandatory.

## Dual 6001 bearing and overhung-pulley load path

- Conservative rating floors come from SKF W 6001-2RS1: 12×28×8 mm, C=4.42 kN, C0=2.36 kN and 16000 r/min limiting speed. This does not claim an SKF purchase.
- Bearing centers are 38 mm apart and the pulley center overhangs the outboard bearing by 14.5 mm. Three-times shock torque plus an 80 N-per-span pretension ceiling creates a 348.5 N pulley envelope and **532.8 N** worst equivalent bearing load.
- Static safety is 4.43; analytical L10 is **9516 h** even at 1000 r/min. Clearance, seals, fits, misalignment, contamination and temperature still require selected-part evidence.

## 12 mm keyed shaft, hubs and positive rail interface

- Under 3.6 N·m shock torque, pulley overhang and 100 N wheel preload, the ideal bending-torsion von Mises stress is 40.1 MPa. A 2.5 keyway factor raises it to **100.2 MPa**. Requiring certified yield of at least 400 MPa gives 3.99 analytical safety.
- A 4×4×20 mm key sees 7.5 MPa shear and 15.0 MPa bearing stress. A physical 7.2 N·m no-slip, no-permanent-set torque proof remains required.
- Each cassette uses two 6 mm dowels, four M6 clamps and a hard stop. At 1000 N interface load, dowel shear is 17.7 MPa, plate bearing 13.9 MPa and tear-out 4.6 MPa. No interface friction is credited.

## Packaging and assembly limits

- Moving to 90 mm center distance leaves 102.0 mm motor clearance, 13.1 mm plate clearance and 20.8 mm guarded-pulley clearance.
- These are local analytical envelopes, not a full current-master clash pass. Stage 22 did not save or overwrite the user's Blender master.

## Maker assembly and verification sequence

1. Cut inexpensive fit-test profiles first and confirm 90 mm center distance, 24T pulleys, the 300 mm belt and removable-pulley installation order.
2. Freeze the 12 mm shaft and 28 mm housing fits from the selected bearing supplier; locate one bearing and allow at least 0.3 mm float at the other, then measure endplay and outer-ring creep.
3. Machine the certified 12 mm keyed shaft and 4×4 keys, and pass the 7.2 N·m bench torque proof before installing the tire.
4. Feed each 1000 N cassette load into the chassis through two dowels and a hard stop; M6 fasteners clamp only. Guard removal must require isolated power.
5. Only then run raised-wheel belt tracking, E-stop, thermal, shell-contact, low-speed yaw-identification and nineteen-item commissioning tests.

Open freeze gates: 13. Manufacturing release is false and physical status is NOT_RUN.

## Official sources

- Gates 5MGT-300-15 product page: https://www.gates.com/us/en/power-transmission/synchronous-belts/poly-chain-synchronous-belts.p.9270-000000-000001.v.9270-06002.html
- Gates 2025 industrial catalog: https://www.gates.com/content/dam/documents-library/catalogs/industrial-power-transmission-catalogue-en.pdf
- Gates PowerGrip GT3 design manual: https://www.gates.com/content/dam/documents-library/catalogs/powergrip-gt3-drive-design-manual-en.pdf
- Gates preventive-maintenance manual: https://www.gates.com/content/dam/gates/home/knowledge-center/resource-library/operating-manuals/preventive-maintenance-manual-en.pdf
- SKF stainless deep-groove ball-bearing catalog: https://www.skf.com/binaries/pub12/Images/0901d19680406705-SKF-Stainless-steel-DGBB---11279_1-EN-Low-Res_tcm_12-259995.pdf
