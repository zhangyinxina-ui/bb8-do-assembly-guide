#!/usr/bin/env python3
"""Generate the deterministic KiCad 10 Stage-19 safety-gate schematic.

The generated schematic embeds the selected KiCad 10 symbols so ERC and
exports do not depend on a project-specific symbol table.  It is still a
reference schematic only: no PCB, routing, Gerber, bench or motion release is
created by this script.
"""

from __future__ import annotations

import argparse
import os
import re
import textwrap
import uuid
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = (
    ROOT
    / "hardware"
    / "stage19_dual_permissive_gate"
    / "stage19_dual_permissive_gate.kicad_sch"
)
CUSTOM_LIBRARY_OUTPUT = OUTPUT.with_name("stage19_symbols.kicad_sym")
PROJECT = "stage19_dual_permissive_gate"
NAMESPACE = uuid.UUID("e718e17d-25bb-5bd1-b2bd-8c84d708c517")
SHEET_UUID = str(uuid.uuid5(NAMESPACE, "sheet:/"))


def deterministic_uuid(key: str) -> str:
    return str(uuid.uuid5(NAMESPACE, key))


def quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def locate_symbol_dir(explicit: Path | None = None) -> Path:
    candidates = [
        explicit,
        Path(os.environ["KICAD_SYMBOL_DIR"]) if os.environ.get("KICAD_SYMBOL_DIR") else None,
        Path.home()
        / "Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
        Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"),
    ]
    for candidate in candidates:
        if candidate and (candidate / "Device.kicad_sym").is_file():
            return candidate.resolve()
    raise FileNotFoundError(
        "KiCad symbol libraries not found; pass --symbol-dir or set KICAD_SYMBOL_DIR"
    )


def extract_top_level_symbol(path: Path, name: str) -> str:
    text = path.read_text(encoding="utf-8")
    marker = f'(symbol "{name}"'
    start = text.find(marker)
    if start < 0:
        raise ValueError(f"{name!r} not found in {path}")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    raise ValueError(f"unterminated symbol {name!r} in {path}")


def _sexpr_blocks(text: str, marker: str) -> list[tuple[int, int, str]]:
    blocks: list[tuple[int, int, str]] = []
    search_from = 0
    while True:
        start = text.find(marker, search_from)
        if start < 0:
            return blocks
        depth = 0
        in_string = False
        escaped = False
        for index in range(start, len(text)):
            char = text[index]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    blocks.append((start, index + 1, text[start : index + 1]))
                    search_from = index + 1
                    break
        else:
            raise ValueError(f"unterminated block beginning with {marker!r}")


def change_pin_type(block: str, pin_number: str, pin_type: str) -> str:
    for start, end, pin_block in _sexpr_blocks(block, "(pin "):
        if re.search(rf'\(number\s+"{re.escape(pin_number)}"', pin_block):
            changed = re.sub(r"^\(pin\s+\w+", f"(pin {pin_type}", pin_block, count=1)
            return block[:start] + changed + block[end:]
    raise ValueError(f"pin {pin_number} not found while changing type")


def embedded_symbol(
    symbol_dir: Path,
    library: str,
    source_name: str,
    embedded_id: str,
    *,
    rename_nested: str | None = None,
    pin_types: dict[str, str] | None = None,
) -> str:
    block = extract_top_level_symbol(symbol_dir / f"{library}.kicad_sym", source_name)
    short_name = embedded_id.split(":", 1)[1]
    if rename_nested:
        block = block.replace(source_name, rename_nested)
        short_name = rename_nested
    block = block.replace(
        f'(symbol "{short_name}"', f'(symbol "{embedded_id}"', 1
    )
    for pin_number, pin_type in (pin_types or {}).items():
        block = change_pin_type(block, pin_number, pin_type)
    return block


def custom_mcu_header_symbol(symbol_dir: Path) -> str:
    block = extract_top_level_symbol(
        symbol_dir / "Connector_Generic.kicad_sym", "Conn_01x06"
    ).replace("Conn_01x06", "MCU_INPUT_HEADER")
    for pin_number in ("1", "3", "5"):
        block = change_pin_type(block, pin_number, "output")
    return block


def custom_opto_symbol(symbol_dir: Path) -> str:
    block = extract_top_level_symbol(
        symbol_dir / "Isolator.kicad_sym", "Optocoupler_DC_PhotoNPN_AKEC"
    ).replace("Optocoupler_DC_PhotoNPN_AKEC", "VO617A-4")
    return change_pin_type(block, "3", "output")


def custom_library(symbol_dir: Path) -> str:
    blocks = [
        textwrap.indent(custom_mcu_header_symbol(symbol_dir), "\t"),
        textwrap.indent(custom_opto_symbol(symbol_dir), "\t"),
    ]
    return "\n".join(
        [
            "(kicad_symbol_lib",
            "\t(version 20251024)",
            '\t(generator "generate_stage19_kicad.py")',
            '\t(generator_version "1.0")',
            *blocks,
            ")",
            "",
        ]
    )


@dataclass(frozen=True)
class Symbol:
    ref: str
    lib_id: str
    value: str
    x: float
    y: float
    pins: tuple[str, ...]
    unit: int = 1
    footprint: str = ""
    datasheet: str = ""
    description: str = ""
    angle: int = 0
    in_bom: bool = True
    on_board: bool = True
    ref_offset: tuple[float, float] = (2.54, -2.54)
    value_offset: tuple[float, float] = (2.54, 0.0)
    hide_reference: bool = False
    hide_value: bool = False


def fmt(value: float) -> str:
    return f"{value:.4f}".rstrip("0").rstrip(".")


def symbol_instance(symbol: Symbol) -> str:
    x = fmt(symbol.x)
    y = fmt(symbol.y)
    key = f"symbol:{symbol.ref}:{symbol.unit}:{x}:{y}"
    yes_no = lambda value: "yes" if value else "no"
    properties = [
        (
            "Reference",
            symbol.ref,
            symbol.x + symbol.ref_offset[0],
            symbol.y + symbol.ref_offset[1],
            symbol.hide_reference,
        ),
        (
            "Value",
            symbol.value,
            symbol.x + symbol.value_offset[0],
            symbol.y + symbol.value_offset[1],
            symbol.hide_value,
        ),
        ("Footprint", symbol.footprint, symbol.x, symbol.y, True),
        ("Datasheet", symbol.datasheet, symbol.x, symbol.y, True),
        ("Description", symbol.description, symbol.x, symbol.y, True),
    ]
    lines = [
        "(symbol",
        f'\t(lib_id "{quote(symbol.lib_id)}")',
        f"\t(at {x} {y} {symbol.angle})",
        f"\t(unit {symbol.unit})",
        "\t(exclude_from_sim no)",
        f"\t(in_bom {yes_no(symbol.in_bom)})",
        f"\t(on_board {yes_no(symbol.on_board)})",
        "\t(dnp no)",
        f'\t(uuid "{deterministic_uuid(key)}")',
    ]
    for name, value, px, py, hidden in properties:
        lines.extend(
            [
                f'\t(property "{name}" "{quote(value)}"',
                f"\t\t(at {fmt(px)} {fmt(py)} {symbol.angle})",
                "\t\t(effects",
                "\t\t\t(font (size 1.0 1.0))",
                *( ["\t\t\t(hide yes)"] if hidden else [] ),
                "\t\t)",
                "\t)",
            ]
        )
    for pin in symbol.pins:
        lines.extend(
            [
                f'\t(pin "{pin}"',
                f'\t\t(uuid "{deterministic_uuid(f"{key}:pin:{pin}")}")',
                "\t)",
            ]
        )
    lines.extend(
        [
            "\t(instances",
            f'\t\t(project "{PROJECT}"',
            f'\t\t\t(path "/{SHEET_UUID}"',
            f'\t\t\t\t(reference "{symbol.ref}")',
            f"\t\t\t\t(unit {symbol.unit})",
            "\t\t\t)",
            "\t\t)",
            "\t)",
            ")",
        ]
    )
    return "\n".join(lines)


def label(net: str, x: float, y: float, key: str, angle: int = 0) -> str:
    justify = "right bottom" if angle == 180 else "left bottom"
    return "\n".join(
        [
            f'(label "{quote(net)}"',
            f"\t(at {fmt(x)} {fmt(y)} {angle})",
            "\t(effects",
            "\t\t(font (size 0.762 0.762))",
            f"\t\t(justify {justify})",
            "\t)",
            f'\t(uuid "{deterministic_uuid(f"label:{key}:{net}:{fmt(x)}:{fmt(y)}")}")',
            ")",
        ]
    )


def note(text: str, x: float, y: float, key: str, size: float = 1.27) -> str:
    return "\n".join(
        [
            f'(text "{quote(text)}"',
            "\t(exclude_from_sim no)",
            f"\t(at {fmt(x)} {fmt(y)} 0)",
            "\t(effects",
            f"\t\t(font (size {fmt(size)} {fmt(size)}))",
            "\t\t(justify left bottom)",
            "\t)",
            f'\t(uuid "{deterministic_uuid(f"text:{key}")}")',
            ")",
        ]
    )


def generate(symbol_dir: Path) -> str:
    embedded = [
        embedded_symbol(symbol_dir, "Device", "R", "Device:R"),
        embedded_symbol(symbol_dir, "Device", "C", "Device:C"),
        embedded_symbol(symbol_dir, "Device", "D", "Device:D"),
        embedded_symbol(
            symbol_dir, "Connector_Generic", "Conn_01x02", "Connector_Generic:Conn_01x02"
        ),
        embedded_symbol(
            symbol_dir, "Connector_Generic", "Conn_01x05", "Connector_Generic:Conn_01x05"
        ),
        embedded_symbol(
            symbol_dir, "Connector_Generic", "Conn_01x06", "BB8_STAGE19:MCU_INPUT_HEADER",
            rename_nested="MCU_INPUT_HEADER",
            pin_types={"1": "output", "3": "output", "5": "output"},
        ),
        embedded_symbol(symbol_dir, "Connector", "TestPoint", "Connector:TestPoint"),
        embedded_symbol(symbol_dir, "power", "PWR_FLAG", "power:PWR_FLAG"),
        embedded_symbol(symbol_dir, "74xGxx", "74LVC2G08", "74xGxx:74LVC2G08"),
        embedded_symbol(
            symbol_dir,
            "Isolator",
            "Optocoupler_DC_PhotoNPN_AKEC",
            "BB8_STAGE19:VO617A-4",
            rename_nested="VO617A-4",
            pin_types={"3": "output"},
        ),
    ]

    labels: list[str] = []
    symbols: list[Symbol] = []
    notes = [
        note("LOGIC POWER AND EXTERNAL INTERFACES", 12.7, 17.78, "interfaces", 1.5),
        note("INDEPENDENT ENERGISE-TO-RUN INPUTS", 12.7, 78.74, "safety_inputs", 1.5),
        note("THREE-STAGE DUAL PWM PERMISSIVE CHAIN", 119.38, 17.78, "logic_chain", 1.5),
        note("U3 / SAFE_A", 134.62, 25.4, "gate_u3", 1.0),
        note("U4 / SAFE_B", 187.96, 25.4, "gate_u4", 1.0),
        note("U5 / ALERT_N", 241.3, 25.4, "gate_u5", 1.0),
        note("FAIL-LOW BIAS, ALERT PULL-UP AND LOCAL DECOUPLING", 119.38, 86.36, "bias", 1.5),
        note("MANDATORY TEST POINTS", 119.38, 137.16, "test_points", 1.5),
        note("SAFETY BOUNDARY", 12.7, 165.1, "boundary", 1.5),
        note(
            "CONNECTIVITY + ERC EVIDENCE ONLY. NO PCB, ROUTING, DRC, GERBER, ASSEMBLY, POWER-UP OR MOTION RELEASE.",
            12.7,
            172.72,
            "boundary_1",
            1.15,
        ),
        note(
            "MDD20A SIGN-MAGNITUDE MODE ONLY: PWM LOW IS BRAKE, NOT ENERGY ISOLATION. UPSTREAM CONTACTOR REMAINS REQUIRED.",
            12.7,
            177.8,
            "boundary_2",
            1.15,
        ),
        note(
            "SAFE_A, SAFE_B, ALERT_N, LOGIC-POWER LOSS AND STUCK-HIGH PWM REQUIRE <=20 ms BENCH WAVEFORMS BEFORE ACTUATOR POWER.",
            12.7,
            182.88,
            "boundary_3",
            1.15,
        ),
    ]

    def add_symbol(symbol: Symbol, pin_nets: dict[str, tuple[str, float, float, int]]) -> None:
        symbols.append(symbol)
        for pin, (net, x, y, angle) in pin_nets.items():
            if pin not in symbol.pins:
                raise ValueError(f"{symbol.ref} unit {symbol.unit}: unknown pin {pin}")
            labels.append(label(net, x, y, f"{symbol.ref}:{symbol.unit}:{pin}", angle))

    def connector(
        ref: str,
        lib_id: str,
        count: int,
        x: float,
        y: float,
        nets: tuple[str, ...],
        value: str,
        footprint: str,
    ) -> None:
        pins = tuple(str(index) for index in range(1, count + 1))
        local_pin_y = {
            2: (0.0, -2.54),
            5: (5.08, 2.54, 0.0, -2.54, -5.08),
            6: (5.08, 2.54, 0.0, -2.54, -5.08, -7.62),
        }[count]
        pin_nets = {
            pin: (nets[index], x - 5.08, y - local_pin_y[index], 180)
            for index, pin in enumerate(pins)
        }
        add_symbol(
            Symbol(
                ref,
                lib_id,
                value,
                x,
                y,
                pins,
                footprint=footprint,
                ref_offset=(2.54, -max(local_pin_y) - 2.54),
                value_offset=(2.54, -min(local_pin_y) + 2.54),
            ),
            pin_nets,
        )

    connector(
        "J1", "Connector_Generic:Conn_01x02", 2, 35.56, 25.4,
        ("3V3", "GND"), "B2B-XH-A / LOGIC POWER",
        "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
    )
    connector(
        "J2", "BB8_STAGE19:MCU_INPUT_HEADER", 6, 35.56, 40.64,
        ("PWM_L_IN", "DIR_L", "PWM_R_IN", "DIR_R", "ALERT_N", "GND"),
        "B6B-XH-A / MCU+ALERT",
        "Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical",
    )
    connector(
        "J3", "Connector_Generic:Conn_01x05", 5, 35.56, 60.96,
        ("PWM_L_OUT", "DIR_L", "PWM_R_OUT", "DIR_R", "GND"),
        "B5B-XH-A / MDD20A",
        "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
    )
    connector(
        "J4", "Connector_Generic:Conn_01x02", 2, 35.56, 91.44,
        ("SAFE_A_PLUS", "SAFE_A_RETURN"), "B2B-XH-A / SAFE A",
        "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
    )
    connector(
        "J5", "Connector_Generic:Conn_01x02", 2, 35.56, 121.92,
        ("SAFE_B_PLUS", "SAFE_B_RETURN"), "B2B-XH-A / SAFE B",
        "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
    )

    for ref, net, x, y in (
        ("#FLG01", "3V3", 20.32, 25.4),
        ("#FLG02", "GND", 20.32, 27.94),
    ):
        add_symbol(
            Symbol(
                ref,
                "power:PWR_FLAG",
                "PWR_FLAG",
                x,
                y,
                ("1",),
                in_bom=False,
                on_board=False,
                hide_reference=True,
                hide_value=True,
            ),
            {"1": (net, x, y, 0)},
        )

    for suffix, y, index in (("A", 91.44, 1), ("B", 121.92, 2)):
        plus = f"SAFE_{suffix}_PLUS"
        return_net = f"SAFE_{suffix}_RETURN"
        led_anode = f"SAFE_{suffix}_LED_A"
        ok_net = f"SAFE_{suffix}_OK"
        add_symbol(
            Symbol(
                f"R{index}", "Device:R", "2.00k 1% 0.5W MIN", 55.88, y,
                ("1", "2"), footprint="Resistor_SMD:R_1210_3225Metric",
                ref_offset=(5.08, -2.54), value_offset=(15.24, 0.0),
            ),
            {
                "1": (plus, 55.88, y - 3.81, 0),
                "2": (led_anode, 55.88, y + 3.81, 0),
            },
        )
        add_symbol(
            Symbol(
                f"D{index}", "Device:D", "1N4148W REVERSE CLAMP", 81.28, y,
                ("1", "2"), footprint="Diode_SMD:D_SOD-123",
                ref_offset=(0.0, -3.81), value_offset=(0.0, 3.81),
            ),
            {
                "1": (led_anode, 77.47, y, 180),
                "2": (return_net, 85.09, y, 0),
            },
        )
        add_symbol(
            Symbol(
                f"U{index}", "BB8_STAGE19:VO617A-4", "VO617A-4", 111.76, y,
                ("1", "2", "3", "4"), footprint="Package_DIP:DIP-4_W7.62mm",
                datasheet="https://www.vishay.com/docs/83430/vo617a.pdf",
                description="Independent energise-to-run optocoupler",
                ref_offset=(0.0, -5.08), value_offset=(0.0, 5.08),
            ),
            {
                "1": (led_anode, 104.14, y - 2.54, 180),
                "2": (return_net, 104.14, y + 2.54, 180),
                "3": (ok_net, 119.38, y + 2.54, 0),
                "4": ("3V3", 119.38, y - 2.54, 0),
            },
        )
        bias_y = 105.41 if suffix == "A" else 128.27
        add_symbol(
            Symbol(
                f"R{index + 2}", "Device:R", "4.70k 1%", 127.0, bias_y,
                ("1", "2"), footprint="Resistor_SMD:R_0805_2012Metric",
                ref_offset=(5.08, -2.54), value_offset=(7.62, 0.0),
            ),
            {
                "1": (ok_net, 127.0, bias_y - 3.81, 0),
                "2": ("GND", 127.0, bias_y + 3.81, 0),
            },
        )

    def gate_package(
        ref: str,
        x: float,
        left_nets: tuple[str, str, str],
        right_nets: tuple[str, str, str],
    ) -> None:
        value = "SN74LVC2G08DCU"
        footprint = "Package_SO:VSSOP-8_2.3x2mm_P0.5mm"
        datasheet = "https://www.ti.com/lit/ds/symlink/sn74lvc2g08.pdf"
        for unit, y, pins, nets in (
            (1, 35.56, ("1", "2", "7"), left_nets),
            (2, 53.34, ("3", "5", "6"), right_nets),
        ):
            input_a, input_b, output = nets
            pin_map = (
                {
                    "1": (input_a, x - 15.24, y - 2.54, 180),
                    "2": (input_b, x - 15.24, y + 2.54, 180),
                    "7": (output, x + 12.7, y, 0),
                }
                if unit == 1
                else {
                    "5": (input_a, x - 15.24, y - 2.54, 180),
                    "6": (input_b, x - 15.24, y + 2.54, 180),
                    "3": (output, x + 12.7, y, 0),
                }
            )
            add_symbol(
                Symbol(
                    ref,
                    "74xGxx:74LVC2G08",
                    value,
                    x,
                    y,
                    pins,
                    unit=unit,
                    footprint=footprint,
                    datasheet=datasheet,
                    ref_offset=(-2.54, -7.62),
                    hide_value=True,
                ),
                pin_map,
            )
        power_y = 71.12
        add_symbol(
            Symbol(
                ref,
                "74xGxx:74LVC2G08",
                value,
                x,
                power_y,
                ("4", "8"),
                unit=3,
                footprint=footprint,
                datasheet=datasheet,
                ref_offset=(6.35, 0.0),
                hide_value=True,
            ),
            {
                "8": ("3V3", x, power_y - 10.16, 0),
                "4": ("GND", x, power_y + 10.16, 0),
            },
        )

    gate_package("U3", 147.32, ("PWM_L_IN", "SAFE_A_OK", "PWM_L_A"),
                 ("PWM_R_IN", "SAFE_A_OK", "PWM_R_A"))
    gate_package("U4", 200.66, ("PWM_L_A", "SAFE_B_OK", "PWM_L_AB"),
                 ("PWM_R_A", "SAFE_B_OK", "PWM_R_AB"))
    gate_package("U5", 254.0, ("PWM_L_AB", "ALERT_N", "PWM_L_OUT"),
                 ("PWM_R_AB", "ALERT_N", "PWM_R_OUT"))

    pulldowns = (
        ("R5", "PWM_L_IN", 147.32),
        ("R6", "PWM_R_IN", 161.29),
        ("R7", "PWM_L_A", 175.26),
        ("R8", "PWM_R_A", 189.23),
        ("R9", "PWM_L_AB", 203.2),
        ("R10", "PWM_R_AB", 217.17),
        ("R11", "PWM_L_OUT", 231.14),
        ("R12", "PWM_R_OUT", 245.11),
    )
    for ref, net, x in pulldowns:
        add_symbol(
            Symbol(
                ref,
                "Device:R",
                "10.0k 1%",
                x,
                101.6,
                ("1", "2"),
                footprint="Resistor_SMD:R_0805_2012Metric",
                ref_offset=(4.0, -1.27),
                value_offset=(5.08, 1.27),
            ),
            {
                "1": (net, x, 97.79, 0),
                "2": ("GND", x, 105.41, 0),
            },
        )
    add_symbol(
        Symbol(
            "R13",
            "Device:R",
            "10.0k 1%",
            264.16,
            101.6,
            ("1", "2"),
            footprint="Resistor_SMD:R_0805_2012Metric",
            ref_offset=(5.08, -2.54),
            value_offset=(7.62, 0.0),
        ),
        {
            "1": ("3V3", 264.16, 97.79, 0),
            "2": ("ALERT_N", 264.16, 105.41, 0),
        },
    )
    for index, x in enumerate((147.32, 200.66, 254.0), start=1):
        add_symbol(
            Symbol(
                f"C{index}",
                "Device:C",
                "100nF X7R 10V MIN",
                x,
                124.46,
                ("1", "2"),
                footprint="Capacitor_SMD:C_0603_1608Metric",
                ref_offset=(5.08, -2.54),
                value_offset=(12.7, 0.0),
            ),
            {
                "1": ("3V3", x, 120.65, 0),
                "2": ("GND", x, 128.27, 0),
            },
        )

    for index, (net, x) in enumerate(
        zip(
            ("SAFE_A_OK", "SAFE_B_OK", "ALERT_N", "PWM_L_OUT", "PWM_R_OUT", "GND"),
            (127.0, 152.4, 177.8, 203.2, 228.6, 254.0),
        ),
        start=1,
    ):
        add_symbol(
            Symbol(
                f"TP{index}", "Connector:TestPoint", net, x, 147.32, ("1",),
                footprint="TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm",
                ref_offset=(1.27, 3.81),
                hide_value=True,
            ),
            {"1": (net, x, 147.32, 0)},
        )

    header = [
        "(kicad_sch",
        "\t(version 20250114)",
        '\t(generator "generate_stage19_kicad.py")',
        '\t(generator_version "1.0")',
        f'\t(uuid "{SHEET_UUID}")',
        '\t(paper "A4")',
        "\t(title_block",
        '\t\t(title "BB-8 Independent Dual-Permissive PWM Gate")',
        '\t\t(date "2026-07-15")',
        '\t\t(rev "S19-A")',
        '\t\t(company "REP-LAB / BB8_DO_Assembly_Guide")',
        '\t\t(comment 1 "REFERENCE DESIGN - NOT RELEASED FOR FABRICATION")',
        '\t\t(comment 2 "PCB, DRC, GERBER, BENCH AND PHYSICAL COMMISSIONING REMAIN NOT_RUN")',
        "\t)",
        "\t(lib_symbols",
    ]
    for block in embedded:
        header.append(textwrap.indent(block, "\t\t"))
    header.append("\t)")
    for item in notes + labels + [symbol_instance(symbol) for symbol in symbols]:
        header.append(textwrap.indent(item, "\t"))
    header.extend(
        [
            "\t(sheet_instances",
            '\t\t(path "/"',
            '\t\t\t(page "1")',
            "\t\t)",
            "\t)",
            "\t(embedded_fonts no)",
            ")",
        ]
    )
    return "\n".join(header) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol-dir", type=Path)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    parser.add_argument("--library-output", type=Path, default=CUSTOM_LIBRARY_OUTPUT)
    args = parser.parse_args()
    symbol_dir = locate_symbol_dir(args.symbol_dir)
    output = args.output.resolve()
    library_output = args.library_output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(generate(symbol_dir), encoding="utf-8", newline="\n")
    library_output.parent.mkdir(parents=True, exist_ok=True)
    library_output.write_text(custom_library(symbol_dir), encoding="utf-8", newline="\n")
    print(f"GENERATED {output}")
    print(f"GENERATED {library_output}")
    print(f"SYMBOL_DIR {symbol_dir}")


if __name__ == "__main__":
    main()
