# BB-8 Stage 16: physical commissioning evidence gate

> Current result: `HOLD_PHYSICAL_TESTS_NOT_RUN`. Stage 16 defines nineteen mandatory physical gates and machine-checks telemetry, measurement limits, evidence files and SHA-256 hashes. All nineteen remain `NOT_RUN`, so the project does not claim that a physical BB-8 has run.

## Why this stage exists

Stages 10–15 cover closed-loop control, sensors, current protection, mass and CoM, drive power, a hard E-stop and an analytical grade envelope. They did not provide one auditable path from real instruments, video, photographs and serial logs to each acceptance decision. Simulation, firmware compilation and Blender geometry are not physical-running proof.

Stage 16 adds three linked contracts:

1. `engineering/commissioning_test_plan.json` defines nineteen tests, required metrics, limits and accepted evidence kinds.
2. `engineering/commissioning_evidence.json` is the real-hardware record for serial number, operator, date, measurements and files.
3. `tools/verify_commissioning_evidence.py` checks coverage, limits, safe relative paths, file existence and SHA-256. A PASS without real files is invalid.

## Nineteen mandatory gates

| Group | Tests | Primary acceptance line |
|---|---|---|
| Mechanical/head | M01, H01 | Mass within the current 10.628 kg envelope, CoM at least 20 mm below centre, ≥40 N pull-off through the installed 8 mm gap |
| Electrical/control | E01–E03, C01 | Dual normally-closed channels, polarity/isolation, hard EN removal, dual INA226 error ≤3%, encoder repeat error ≤1% |
| Drive/thermal | D01–D02, T01–T02 | Raised-wheel no-load run, controlled stall cutoff ≤300 ms, 20 min open and 15 min sealed thermal runs |
| Ground | G01–G04 | 5 m at 0.10 m/s, 0.8 m turn, E-stop distance ≤0.50 m from 0.30 m/s, powered 3° ramp |
| Fault/power | F01–F02, P01 | Lost command and stale IMU/encoder/current data all remove EN; regenerative bus peak ≤16.8 V |
| Service/final | S01, L01 | Twenty damage-free service cycles; only then a ten-minute integrated run inside soft barriers |

These are conservative first-run limits for the current design envelope. If the final motor driver, fuse, contactor, battery or BMS rating is lower, the lower device limit governs.

## Physical telemetry

The ESP32 now emits a timestamped fixed field set every 200 ms: enable, fault, commanded motion, battery, temperature, E-stop, remote state, IMU, encoders, tilt, yaw, wheel speeds, motor currents, power readiness, hardware trip and PWM. Convert a preserved serial-monitor log with:

This telemetry build compiles for Arduino-ESP32 3.3.10 / Generic ESP32-S3 at 370,095 program bytes (28%) and 24,676 global bytes (7%). Compilation is not board-upload or powered-test evidence.

```bash
python3 tools/parse_bb8_telemetry.py \
  --input evidence/run-001/serial.log \
  --output evidence/run-001/telemetry.csv \
  --summary evidence/run-001/telemetry_summary.json
```

The parser rejects missing fields, non-finite values and non-increasing timestamps. It does not promote telemetry to PASS; each gate still needs the required camera, instrument or measurement evidence.

## Recording and verification

1. Create one directory for each real run, such as `evidence/BB8-001/2026-07-12-G01/`.
2. Preserve untouched serial logs, video/photos and instrument exports.
3. Hash every file and add its relative path, kind and SHA-256 to the corresponding evidence record.
4. Enter measured metrics and use only `NOT_RUN`, `BLOCKED`, `PASS` or `FAIL`.
5. Run `python3 tools/verify_commissioning_evidence.py`; incomplete real hardware must remain `HOLD_PHYSICAL_TESTS_NOT_RUN`.
6. `--require-pass` can succeed only when all nineteen mandatory records have matching real files, compliant metrics, a hardware serial, operator and date.

## Anti-false-PASS regression

- The current blank real-hardware template must evaluate to HOLD.
- Changing every status to PASS without metrics and files must evaluate to `INVALID_EVIDENCE`.
- Synthetic data can exercise the evaluator only inside its test-only hidden mode; normal audits reject `SYNTHETIC_TEST_ONLY`.

## Boundary that remains

- No physical BB-8 has been assembled and connected within this project, so every gate remains `NOT_RUN`.
- There is no mechanical parking brake; G04 covers powered grade motion, never unpowered holding.
- Final driver, fuse, contactor, BMS and battery choices must be frozen against their data sheets and measured currents before powered testing.
- L01 is not a first test. It follows the other eighteen gates and requires soft barriers, a wired tether E-stop and an observer.
