#!/usr/bin/env python3
"""Generate and route the Stage-19 dual-permissive-gate KiCad PCB.

This script must be run with KiCad's bundled Python because it uses pcbnew.
The resulting board is a digital design-review artifact, not a fabrication
release.  Physical peer review, Gerber review, assembly, continuity and bench
tests remain explicit release gates elsewhere in the project.
"""

from __future__ import annotations

import argparse
import csv
import heapq
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import pcbnew


ROOT = Path(__file__).resolve().parents[1]
PROJECT_DIR = ROOT / "hardware" / "stage19_dual_permissive_gate"
CANONICAL_NETLIST = ROOT / "engineering" / "stage19_gate_netlist.csv"
DEFAULT_OUTPUT = PROJECT_DIR / "stage19_dual_permissive_gate.kicad_pcb"

BOARD_LEFT = 100.0
BOARD_TOP = 100.0
BOARD_RIGHT = 150.0
BOARD_BOTTOM = 135.0
GRID_MM = 0.10
TRACK_WIDTH_MM = 0.20
CLEARANCE_MM = 0.15
VIA_DIAMETER_MM = 0.60
VIA_DRILL_MM = 0.30
EDGE_KEEP_MM = 0.55

F_CU = pcbnew.F_Cu
B_CU = pcbnew.B_Cu
LAYERS = (F_CU, B_CU)


@dataclass(frozen=True)
class Placement:
    footprint: str
    value: str
    x: float
    y: float
    rotation: float = 0.0


PLACEMENTS: dict[str, Placement] = {
    "J1": Placement(
        "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "LOGIC POWER 3V3",
        134.5,
        103.8,
    ),
    "J2": Placement(
        "Connector_JST:JST_XH_B6B-XH-A_1x06_P2.50mm_Vertical",
        "MCU PWM DIR ALERT",
        103.7,
        110.0,
        270.0,
    ),
    "J3": Placement(
        "Connector_JST:JST_XH_B5B-XH-A_1x05_P2.50mm_Vertical",
        "MDD20A PWM DIR",
        146.2,
        110.5,
        270.0,
    ),
    "J4": Placement(
        "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "SAFE A 12-16V8",
        111.5,
        103.8,
    ),
    "J5": Placement(
        "Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical",
        "SAFE B 12-16V8",
        110.0,
        130.7,
    ),
    "U1": Placement("Package_DIP:DIP-4_W7.62mm", "VO617A-4", 119.0, 103.8),
    "U2": Placement("Package_DIP:DIP-4_W7.62mm", "VO617A-4", 119.0, 128.2),
    "U3": Placement(
        "Package_SO:VSSOP-8_2.3x2mm_P0.5mm", "SN74LVC2G08DCU", 116.5, 112.5
    ),
    "U4": Placement(
        "Package_SO:VSSOP-8_2.3x2mm_P0.5mm", "SN74LVC2G08DCU", 126.5, 117.5
    ),
    "U5": Placement(
        "Package_SO:VSSOP-8_2.3x2mm_P0.5mm", "SN74LVC2G08DCU", 136.5, 112.5
    ),
    "R1": Placement("Resistor_SMD:R_1210_3225Metric", "2.00k 1% 0.5W", 108.5, 110.5, 90.0),
    "R2": Placement("Resistor_SMD:R_1210_3225Metric", "2.00k 1% 0.5W", 108.5, 124.0, 90.0),
    "R3": Placement("Resistor_SMD:R_0805_2012Metric", "4.70k 1%", 127.0, 114.0),
    "R4": Placement("Resistor_SMD:R_0805_2012Metric", "4.70k 1%", 127.0, 124.5),
    "R5": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 111.0, 115.5),
    "R6": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 111.0, 119.0),
    "R7": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 121.5, 110.5),
    "R8": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 121.5, 115.0),
    "R9": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 131.5, 115.0),
    "R10": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 131.5, 120.0),
    "R11": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 140.0, 109.0),
    "R12": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 140.0, 118.5),
    "R13": Placement("Resistor_SMD:R_0805_2012Metric", "10.0k 1%", 131.5, 108.8),
    "C1": Placement("Capacitor_SMD:C_0603_1608Metric", "100nF", 116.5, 109.0),
    "C2": Placement("Capacitor_SMD:C_0603_1608Metric", "100nF", 123.5, 122.0),
    "C3": Placement("Capacitor_SMD:C_0603_1608Metric", "100nF", 136.5, 109.0),
    "D1": Placement("Diode_SMD:D_SOD-123", "1N4148W", 111.5, 110.5, 90.0),
    "D2": Placement("Diode_SMD:D_SOD-123", "1N4148W", 111.5, 124.5, 90.0),
    "TP1": Placement("TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm", "SAFE_A_OK", 127.5, 109.8),
    "TP2": Placement("TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm", "SAFE_B_OK", 130.8, 132.3),
    "TP3": Placement("TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm", "ALERT_N", 135.0, 132.3),
    "TP4": Placement("TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm", "PWM_L_OUT", 139.2, 132.3),
    "TP5": Placement("TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm", "PWM_R_OUT", 140.5, 126.0),
    "TP6": Placement("TestPoint:TestPoint_Loop_D2.50mm_Drill1.0mm", "GND", 116.0, 121.0),
}

MOUNTING_HOLES = {
    "H1": (103.0, 103.0),
    "H2": (147.0, 103.0),
    "H3": (103.0, 132.0),
    "H4": (147.0, 132.0),
}

ROUTE_ORDER = (
    "PWM_L_IN",
    "PWM_R_IN",
    "ALERT_N",
    "SAFE_A_OK",
    "SAFE_B_OK",
    "PWM_L_A",
    "PWM_R_A",
    "PWM_L_AB",
    "PWM_R_AB",
    "PWM_L_OUT",
    "PWM_R_OUT",
    "SAFE_A_PLUS",
    "SAFE_A_LED_A",
    "SAFE_A_RETURN",
    "SAFE_B_PLUS",
    "SAFE_B_LED_A",
    "SAFE_B_RETURN",
    "GND",
    "3V3",
    "DIR_L",
    "DIR_R",
)

ROUTE_PAIR_OVERRIDES: dict[str, tuple[tuple[tuple[str, str], tuple[str, str]], ...]] = {
    "ALERT_N": (
        (("U5", "2"), ("R13", "2")),
        (("U5", "6"), ("R13", "2")),
        (("J2", "5"), ("R13", "2")),
        (("TP3", "1"), ("R13", "2")),
    ),
    "SAFE_A_OK": (
        (("U3", "2"), ("R3", "1")),
        (("U3", "6"), ("R3", "1")),
        (("U1", "3"), ("R3", "1")),
        (("TP1", "1"), ("R3", "1")),
    ),
    "SAFE_B_OK": (
        (("U4", "2"), ("R4", "1")),
        (("U4", "6"), ("R4", "1")),
        (("U2", "3"), ("R4", "1")),
        (("TP2", "1"), ("R4", "1")),
    ),
}


def mm(value: int) -> float:
    return pcbnew.ToMM(value)


def grid_index(value_mm: float) -> int:
    return int(round(value_mm / GRID_MM))


def grid_floor(value_mm: float) -> int:
    return int(math.floor(value_mm / GRID_MM + 1e-9))


def grid_ceil(value_mm: float) -> int:
    return int(math.ceil(value_mm / GRID_MM - 1e-9))


def grid_point(ix: int, iy: int) -> tuple[float, float]:
    return ix * GRID_MM, iy * GRID_MM


def iter_disk(cx: float, cy: float, radius: float) -> Iterable[tuple[int, int]]:
    min_x = grid_index(cx - radius)
    max_x = grid_index(cx + radius)
    min_y = grid_index(cy - radius)
    max_y = grid_index(cy + radius)
    radius_sq = radius * radius + 1e-9
    for ix in range(min_x, max_x + 1):
        for iy in range(min_y, max_y + 1):
            x, y = grid_point(ix, iy)
            if (x - cx) ** 2 + (y - cy) ** 2 <= radius_sq:
                yield ix, iy


def iter_segment_cells(
    start: tuple[float, float], end: tuple[float, float], radius: float
) -> Iterable[tuple[int, int]]:
    x1, y1 = start
    x2, y2 = end
    length = math.hypot(x2 - x1, y2 - y1)
    steps = max(1, int(math.ceil(length / (GRID_MM * 0.45))))
    seen: set[tuple[int, int]] = set()
    for step in range(steps + 1):
        ratio = step / steps
        cx = x1 + (x2 - x1) * ratio
        cy = y1 + (y2 - y1) * ratio
        for cell in iter_disk(cx, cy, radius):
            if cell not in seen:
                seen.add(cell)
                yield cell


def canonical_connections() -> dict[tuple[str, str], str]:
    with CANONICAL_NETLIST.open(encoding="utf-8", newline="") as handle:
        return {
            (row["reference"], row["pin"]): row["net"]
            for row in csv.DictReader(handle)
        }


def library_paths() -> dict[str, Path]:
    shared = Path(pcbnew.__file__).resolve().parents[4] / "SharedSupport" / "footprints"
    if not shared.is_dir():
        # KiCad's macOS framework layout can move pcbnew one level deeper.
        candidates = list(Path.home().glob("Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"))
        if not candidates:
            raise FileNotFoundError("KiCad footprint libraries were not found")
        shared = candidates[0]
    return {path.stem: path for path in shared.glob("*.pretty")}


def load_footprint(libraries: dict[str, Path], identifier: str) -> pcbnew.FOOTPRINT:
    library, name = identifier.split(":", 1)
    footprint = pcbnew.FootprintLoad(str(libraries[library]), name)
    if footprint is None:
        raise FileNotFoundError(f"footprint not found: {identifier}")
    return footprint


def add_outline(board: pcbnew.BOARD) -> None:
    corners = (
        (BOARD_LEFT, BOARD_TOP),
        (BOARD_RIGHT, BOARD_TOP),
        (BOARD_RIGHT, BOARD_BOTTOM),
        (BOARD_LEFT, BOARD_BOTTOM),
        (BOARD_LEFT, BOARD_TOP),
    )
    for start, end in zip(corners, corners[1:]):
        segment = pcbnew.PCB_SHAPE(board)
        segment.SetShape(pcbnew.SHAPE_T_SEGMENT)
        segment.SetLayer(pcbnew.Edge_Cuts)
        segment.SetStart(pcbnew.VECTOR2I_MM(*start))
        segment.SetEnd(pcbnew.VECTOR2I_MM(*end))
        segment.SetWidth(pcbnew.FromMM(0.05))
        board.Add(segment)


def add_text(
    board: pcbnew.BOARD,
    text: str,
    x: float,
    y: float,
    layer: int = pcbnew.F_SilkS,
    size: float = 0.8,
) -> None:
    item = pcbnew.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(pcbnew.VECTOR2I_MM(x, y))
    item.SetLayer(layer)
    item.SetTextSize(pcbnew.VECTOR2I_MM(size, size))
    item.SetTextThickness(pcbnew.FromMM(max(0.12, size * 0.16)))
    board.Add(item)


class Router:
    def __init__(self, board: pcbnew.BOARD, footprints: dict[str, pcbnew.FOOTPRINT]):
        self.board = board
        self.footprints = footprints
        self.pad_obstacles: dict[int, dict[tuple[int, int], set[str]]] = {
            F_CU: defaultdict(set),
            B_CU: defaultdict(set),
        }
        self.route_obstacles: dict[int, dict[tuple[int, int], set[str]]] = {
            F_CU: defaultdict(set),
            B_CU: defaultdict(set),
        }
        self.routed_lengths: dict[str, float] = defaultdict(float)
        self.via_counts: dict[str, int] = defaultdict(int)
        self.via_points: set[tuple[str, int, int]] = set()
        self.via_locations: dict[str, list[tuple[float, float]]] = defaultdict(list)
        self.fanout_points: dict[tuple[str, str], tuple[float, float]] = {}
        self._index_pad_obstacles()

    def _index_pad_obstacles(self) -> None:
        expansion = CLEARANCE_MM + TRACK_WIDTH_MM / 2.0
        for reference, footprint in self.footprints.items():
            for pad in footprint.Pads():
                net_name = pad.GetNetname() or f"#NO_NET_{reference}_{pad.GetNumber()}"
                box = pad.GetBoundingBox()
                left = mm(box.GetX()) - expansion
                top = mm(box.GetY()) - expansion
                right = mm(box.GetRight()) + expansion
                bottom = mm(box.GetBottom()) + expansion
                for layer in LAYERS:
                    if not pad.IsOnLayer(layer):
                        continue
                    for ix in range(grid_ceil(left), grid_floor(right) + 1):
                        for iy in range(grid_ceil(top), grid_floor(bottom) + 1):
                            self.pad_obstacles[layer][(ix, iy)].add(net_name)

        mechanical_radius = 1.6 + 0.25 + TRACK_WIDTH_MM / 2.0
        for x, y in MOUNTING_HOLES.values():
            for layer in LAYERS:
                for cell in iter_disk(x, y, mechanical_radius):
                    self.pad_obstacles[layer][cell].add("#MECHANICAL")

    def pad(self, reference: str, number: str) -> pcbnew.PAD:
        for pad in self.footprints[reference].Pads():
            if pad.GetNumber() == number:
                return pad
        raise KeyError(f"pad not found: {reference}.{number}")

    def _inside(self, ix: int, iy: int) -> bool:
        x, y = grid_point(ix, iy)
        return (
            BOARD_LEFT + EDGE_KEEP_MM <= x <= BOARD_RIGHT - EDGE_KEEP_MM
            and BOARD_TOP + EDGE_KEEP_MM <= y <= BOARD_BOTTOM - EDGE_KEEP_MM
        )

    def _blocked(self, state: tuple[int, int, int], net_name: str) -> bool:
        ix, iy, layer = state
        if not self._inside(ix, iy):
            return True
        pad_nets = self.pad_obstacles[layer].get((ix, iy), set())
        if any(owner != net_name for owner in pad_nets):
            return True
        route_owners = self.route_obstacles[layer].get((ix, iy), set())
        return any(owner != net_name for owner in route_owners)

    @staticmethod
    def _pad_layers(pad: pcbnew.PAD) -> tuple[int, ...]:
        return tuple(layer for layer in LAYERS if pad.IsOnLayer(layer))

    @staticmethod
    def _pad_center(pad: pcbnew.PAD) -> tuple[float, float]:
        center = pad.GetCenter()
        return mm(center.x), mm(center.y)

    def _a_star(
        self,
        start_points: list[tuple[int, int, int]],
        goal_points: set[tuple[int, int, int]],
        net_name: str,
    ) -> list[tuple[int, int, int]]:
        if not goal_points:
            raise ValueError("route has no goal")
        goal_xy = {(ix, iy) for ix, iy, _layer in goal_points}
        min_goal_x = min(ix for ix, _iy in goal_xy)
        max_goal_x = max(ix for ix, _iy in goal_xy)
        min_goal_y = min(iy for _ix, iy in goal_xy)
        max_goal_y = max(iy for _ix, iy in goal_xy)

        def heuristic(state: tuple[int, int, int]) -> float:
            ix, iy, layer = state
            dx = 0 if min_goal_x <= ix <= max_goal_x else min(abs(ix - min_goal_x), abs(ix - max_goal_x))
            dy = 0 if min_goal_y <= iy <= max_goal_y else min(abs(iy - min_goal_y), abs(iy - max_goal_y))
            layer_penalty = 0.0 if any(goal[2] == layer for goal in goal_points) else 16.0
            return math.hypot(dx, dy) + layer_penalty

        frontier: list[tuple[float, float, tuple[int, int, int]]] = []
        came_from: dict[tuple[int, int, int], tuple[int, int, int] | None] = {}
        cost_so_far: dict[tuple[int, int, int], float] = {}
        for start in start_points:
            heapq.heappush(frontier, (heuristic(start), 0.0, start))
            came_from[start] = None
            cost_so_far[start] = 0.0

        directions = (
            (1, 0, 1.0),
            (-1, 0, 1.0),
            (0, 1, 1.0),
            (0, -1, 1.0),
            (1, 1, math.sqrt(2.0)),
            (1, -1, math.sqrt(2.0)),
            (-1, 1, math.sqrt(2.0)),
            (-1, -1, math.sqrt(2.0)),
        )
        expanded = 0
        while frontier:
            _priority, current_cost, current = heapq.heappop(frontier)
            if current_cost != cost_so_far.get(current):
                continue
            if current in goal_points:
                path: list[tuple[int, int, int]] = []
                cursor: tuple[int, int, int] | None = current
                while cursor is not None:
                    path.append(cursor)
                    cursor = came_from[cursor]
                return list(reversed(path))
            expanded += 1
            if expanded > 900_000:
                break
            ix, iy, layer = current
            for dx, dy, move_cost in directions:
                neighbour = (ix + dx, iy + dy, layer)
                if neighbour not in goal_points and self._blocked(neighbour, net_name):
                    continue
                new_cost = current_cost + move_cost
                if new_cost < cost_so_far.get(neighbour, math.inf):
                    cost_so_far[neighbour] = new_cost
                    came_from[neighbour] = current
                    heapq.heappush(
                        frontier,
                        (new_cost + heuristic(neighbour), new_cost, neighbour),
                    )

            other_layer = B_CU if layer == F_CU else F_CU
            via_state = (ix, iy, other_layer)
            if (
                (via_state in goal_points or not self._blocked(via_state, net_name))
                and not self._blocked(current, net_name)
                and self._via_clear(ix, iy, net_name)
            ):
                new_cost = current_cost + 22.0
                if new_cost < cost_so_far.get(via_state, math.inf):
                    cost_so_far[via_state] = new_cost
                    came_from[via_state] = current
                    heapq.heappush(
                        frontier,
                        (new_cost + heuristic(via_state), new_cost, via_state),
                    )
        raise RuntimeError(
            f"A* could not route {net_name}: starts={[(s, self._blocked(s, net_name), self._via_clear(s[0], s[1], net_name)) for s in start_points]} "
            f"goals={[(g, self._blocked(g, net_name), self._via_clear(g[0], g[1], net_name)) for g in sorted(goal_points)]}"
        )

    def _via_clear(self, ix: int, iy: int, net_name: str) -> bool:
        x, y = grid_point(ix, iy)
        for reference in ("U3", "U4", "U5"):
            position = self.footprints[reference].GetPosition()
            if math.hypot(x - mm(position.x), y - mm(position.y)) < 3.0:
                return False
        # The pad and route maps are already expanded for a track centre.  A via
        # centre needs only the additional radius delta here; using the full
        # via-to-copper distance would double-count the clearance envelope.
        radius = VIA_DIAMETER_MM / 2.0 - TRACK_WIDTH_MM / 2.0 + 0.08
        for cell in iter_disk(x, y, radius):
            for layer in LAYERS:
                pad_nets = self.pad_obstacles[layer].get(cell, set())
                if any(owner != net_name for owner in pad_nets):
                    return False
                route_owners = self.route_obstacles[layer].get(cell, set())
                if any(owner != net_name for owner in route_owners):
                    return False
        return True

    def _add_track(
        self,
        net: pcbnew.NETINFO_ITEM,
        layer: int,
        start: tuple[float, float],
        end: tuple[float, float],
    ) -> None:
        if math.dist(start, end) < 1e-6:
            return
        track = pcbnew.PCB_TRACK(self.board)
        track.SetStart(pcbnew.VECTOR2I_MM(*start))
        track.SetEnd(pcbnew.VECTOR2I_MM(*end))
        track.SetWidth(pcbnew.FromMM(TRACK_WIDTH_MM))
        track.SetLayer(layer)
        track.SetNet(net)
        self.board.Add(track)
        self.routed_lengths[net.GetNetname()] += math.dist(start, end)
        obstacle_radius = TRACK_WIDTH_MM + CLEARANCE_MM + 0.05
        for cell in iter_segment_cells(start, end, obstacle_radius):
            self.route_obstacles[layer][cell].add(net.GetNetname())

    def _add_via(self, net: pcbnew.NETINFO_ITEM, point: tuple[float, float]) -> None:
        key = (net.GetNetname(), grid_index(point[0]), grid_index(point[1]))
        if key in self.via_points:
            return
        for existing in self.via_locations[net.GetNetname()]:
            if math.dist(existing, point) < VIA_DRILL_MM + 0.25:
                self._add_track(net, F_CU, point, existing)
                self._add_track(net, B_CU, point, existing)
                return
        self.via_points.add(key)
        self.via_locations[net.GetNetname()].append(point)
        via = pcbnew.PCB_VIA(self.board)
        via.SetPosition(pcbnew.VECTOR2I_MM(*point))
        via.SetWidth(pcbnew.FromMM(VIA_DIAMETER_MM))
        via.SetDrill(pcbnew.FromMM(VIA_DRILL_MM))
        via.SetLayerPair(F_CU, B_CU)
        via.SetNet(net)
        self.board.Add(via)
        self.via_counts[net.GetNetname()] += 1
        radius = VIA_DIAMETER_MM / 2.0 + CLEARANCE_MM + TRACK_WIDTH_MM / 2.0
        for cell in iter_disk(*point, radius):
            for layer in LAYERS:
                self.route_obstacles[layer][cell].add(net.GetNetname())

    def _fanout_point(self, pad: pcbnew.PAD) -> tuple[float, float]:
        footprint = pad.GetParentFootprint()
        reference = footprint.GetReference()
        key = (reference, pad.GetNumber())
        center = self._pad_center(pad)
        if reference not in {"U3", "U4", "U5"}:
            return center
        if key in self.fanout_points:
            return self.fanout_points[key]
        footprint_position = footprint.GetPosition()
        footprint_x = mm(footprint_position.x)
        direction = -1.0 if center[0] < footprint_x else 1.0
        pin = int(pad.GetNumber())
        escape_distance = {
            1: 3.0,
            2: 3.5,
            3: 4.0,
            4: 4.5,
            5: 4.5,
            6: 4.0,
            7: 3.5,
            8: 3.0,
        }[pin]
        endpoint = (footprint_x + direction * escape_distance, center[1])
        self._add_track(self.board.FindNet(pad.GetNetname()), F_CU, center, endpoint)
        self.fanout_points[key] = endpoint
        return endpoint

    @staticmethod
    def _compress_path(
        path: list[tuple[int, int, int]]
    ) -> list[tuple[int, int, int]]:
        if len(path) <= 2:
            return path
        compressed = [path[0]]
        previous_direction: tuple[int, int, int] | None = None
        for index in range(1, len(path)):
            previous = path[index - 1]
            current = path[index]
            direction = (
                current[0] - previous[0],
                current[1] - previous[1],
                current[2] - previous[2],
            )
            if previous_direction is not None and direction != previous_direction:
                compressed.append(previous)
            previous_direction = direction
        compressed.append(path[-1])
        return compressed

    def route_pad_pair(self, net_name: str, start_pad: pcbnew.PAD, goal_pad: pcbnew.PAD) -> None:
        net = self.board.FindNet(net_name)
        start_xy = self._fanout_point(start_pad)
        goal_xy = self._fanout_point(goal_pad)
        start_ix, start_iy = grid_index(start_xy[0]), grid_index(start_xy[1])
        goal_ix, goal_iy = grid_index(goal_xy[0]), grid_index(goal_xy[1])
        start_layers = (F_CU,) if start_xy != self._pad_center(start_pad) else self._pad_layers(start_pad)
        goal_layers = (F_CU,) if goal_xy != self._pad_center(goal_pad) else self._pad_layers(goal_pad)
        starts = [(start_ix, start_iy, layer) for layer in start_layers]
        goals = {(goal_ix, goal_iy, layer) for layer in goal_layers}
        path = self._compress_path(self._a_star(starts, goals, net_name))

        first_xy = grid_point(path[0][0], path[0][1])
        self._add_track(net, path[0][2], start_xy, first_xy)
        for previous, current in zip(path, path[1:]):
            previous_xy = grid_point(previous[0], previous[1])
            current_xy = grid_point(current[0], current[1])
            if previous[2] != current[2]:
                self._add_via(net, previous_xy)
            else:
                self._add_track(net, previous[2], previous_xy, current_xy)
        last_xy = grid_point(path[-1][0], path[-1][1])
        self._add_track(net, path[-1][2], last_xy, goal_xy)

    def route_net(self, net_name: str, pads: list[pcbnew.PAD]) -> None:
        if len(pads) < 2:
            return
        if net_name in ROUTE_PAIR_OVERRIDES:
            for start, goal in ROUTE_PAIR_OVERRIDES[net_name]:
                self.route_pad_pair(
                    net_name,
                    self.pad(*start),
                    self.pad(*goal),
                )
            return
        def priority(index: int) -> tuple[int, str, int]:
            reference = pads[index].GetParentFootprint().GetReference()
            family = reference[:1]
            rank = {"U": 0, "J": 1, "D": 2, "T": 2, "R": 3, "C": 3}.get(family, 4)
            return rank, reference, int(pads[index].GetNumber() or 0)

        ordered = sorted(range(len(pads)), key=priority)
        connected = {ordered[0]}
        remaining = set(ordered[1:])
        if remaining:
            first = min(remaining, key=priority)
            self.route_pad_pair(net_name, pads[first], pads[ordered[0]])
            remaining.remove(first)
            connected.add(first)
        while remaining:
            candidate = min(
                (
                    math.dist(self._pad_center(pads[source]), self._pad_center(pads[target])),
                    source,
                    target,
                )
                for source in remaining
                for target in connected
            )
            _distance, source, target = candidate
            self.route_pad_pair(net_name, pads[source], pads[target])
            remaining.remove(source)
            connected.add(source)

    def connect_smd_ground_to_plane(self, pad: pcbnew.PAD) -> None:
        net = self.board.FindNet("GND")
        start_xy = self._fanout_point(pad)
        start_state = (grid_index(start_xy[0]), grid_index(start_xy[1]), F_CU)
        candidates: list[tuple[float, int, int]] = []
        for radius_steps in range(7, 24):
            for dx in range(-radius_steps, radius_steps + 1):
                for dy in (-radius_steps, radius_steps):
                    candidates.append((math.hypot(dx, dy), start_state[0] + dx, start_state[1] + dy))
            for dy in range(-radius_steps + 1, radius_steps):
                for dx in (-radius_steps, radius_steps):
                    candidates.append((math.hypot(dx, dy), start_state[0] + dx, start_state[1] + dy))
            viable = [
                (distance, ix, iy)
                for distance, ix, iy in candidates
                if self._inside(ix, iy)
                and not self._blocked((ix, iy, F_CU), "GND")
                and not self._blocked((ix, iy, B_CU), "GND")
                and self._via_clear(ix, iy, "GND")
            ]
            if viable:
                _distance, ix, iy = min(viable)
                goal = {(ix, iy, F_CU)}
                path = self._compress_path(self._a_star([start_state], goal, "GND"))
                first_xy = grid_point(path[0][0], path[0][1])
                self._add_track(net, F_CU, start_xy, first_xy)
                for previous, current in zip(path, path[1:]):
                    previous_xy = grid_point(previous[0], previous[1])
                    current_xy = grid_point(current[0], current[1])
                    self._add_track(net, F_CU, previous_xy, current_xy)
                via_xy = grid_point(ix, iy)
                self._add_via(net, via_xy)
                return
        raise RuntimeError(f"no ground-via location found for {pad.GetParentFootprint().GetReference()}.{pad.GetNumber()}")


def add_zone(board: pcbnew.BOARD, net_name: str, layer: int) -> None:
    zone = pcbnew.ZONE(board)
    zone.SetLayer(layer)
    zone.SetNet(board.FindNet(net_name))
    zone.SetLocalClearance(pcbnew.FromMM(CLEARANCE_MM))
    zone.SetMinThickness(pcbnew.FromMM(0.20))
    polygon = pcbnew.SHAPE_LINE_CHAIN()
    inset = 0.60
    for point in (
        (BOARD_LEFT + inset, BOARD_TOP + inset),
        (BOARD_RIGHT - inset, BOARD_TOP + inset),
        (BOARD_RIGHT - inset, BOARD_BOTTOM - inset),
        (BOARD_LEFT + inset, BOARD_BOTTOM - inset),
    ):
        polygon.Append(pcbnew.VECTOR2I_MM(*point))
    polygon.SetClosed(True)
    zone.AddPolygon(polygon)
    board.Add(zone)


def build_board(output: Path) -> dict[str, object]:
    connections = canonical_connections()
    libraries = library_paths()
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(2)
    settings = board.GetDesignSettings()
    settings.m_MinClearance = pcbnew.FromMM(CLEARANCE_MM)
    settings.m_TrackMinWidth = pcbnew.FromMM(TRACK_WIDTH_MM)
    settings.m_ViasMinSize = pcbnew.FromMM(VIA_DIAMETER_MM)
    settings.m_ViasMinAnnularWidth = pcbnew.FromMM((VIA_DIAMETER_MM - VIA_DRILL_MM) / 2.0)
    settings.m_HoleClearance = pcbnew.FromMM(0.20)
    settings.m_HoleToHoleMin = pcbnew.FromMM(0.25)
    settings.m_CopperEdgeClearance = pcbnew.FromMM(0.40)
    settings.SetCustomTrackWidth(pcbnew.FromMM(TRACK_WIDTH_MM))
    settings.SetCustomViaSize(pcbnew.FromMM(VIA_DIAMETER_MM))
    settings.SetCustomViaDrill(pcbnew.FromMM(VIA_DRILL_MM))
    settings.UseCustomTrackViaSize(True)
    default_netclass = board.GetAllNetClasses()["Default"]
    default_netclass.SetClearance(pcbnew.FromMM(CLEARANCE_MM))
    default_netclass.SetTrackWidth(pcbnew.FromMM(TRACK_WIDTH_MM))
    default_netclass.SetViaDiameter(pcbnew.FromMM(VIA_DIAMETER_MM))
    default_netclass.SetViaDrill(pcbnew.FromMM(VIA_DRILL_MM))

    net_names = sorted(set(connections.values()))
    nets: dict[str, pcbnew.NETINFO_ITEM] = {}
    for net_name in net_names:
        net = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(net)
        nets[net_name] = net

    footprints: dict[str, pcbnew.FOOTPRINT] = {}
    pads_by_net: dict[str, list[pcbnew.PAD]] = defaultdict(list)
    for reference, placement in PLACEMENTS.items():
        footprint = load_footprint(libraries, placement.footprint)
        footprint.SetReference(reference)
        footprint.SetValue(placement.value)
        footprint.SetPosition(pcbnew.VECTOR2I_MM(placement.x, placement.y))
        footprint.SetOrientationDegrees(placement.rotation)
        footprint.Reference().SetLayer(pcbnew.F_Fab)
        footprint.Reference().SetVisible(True)
        board.Add(footprint)
        footprints[reference] = footprint
        for pad in footprint.Pads():
            key = (reference, pad.GetNumber())
            if key not in connections:
                raise KeyError(f"canonical netlist has no entry for {reference}.{pad.GetNumber()}")
            net_name = connections[key]
            pad.SetNet(nets[net_name])
            pads_by_net[net_name].append(pad)

    for reference, (x, y) in MOUNTING_HOLES.items():
        footprint = load_footprint(libraries, "MountingHole:MountingHole_3.2mm_M3")
        footprint.SetReference(reference)
        footprint.SetValue("M3 INSULATED")
        footprint.SetPosition(pcbnew.VECTOR2I_MM(x, y))
        footprint.Reference().SetLayer(pcbnew.F_Fab)
        board.Add(footprint)
        footprints[reference] = footprint

    add_outline(board)
    add_text(board, "BB-8 STAGE 19 PWM GATE", 125.0, 101.0, layer=pcbnew.F_Fab, size=0.8)
    add_text(board, "REFERENCE ONLY / NO FAB", 125.0, 134.0, layer=pcbnew.F_Fab, size=0.8)
    add_text(board, "SAFE A", 109.0, 109.0, layer=pcbnew.F_Fab, size=0.8)
    add_text(board, "SAFE B", 109.0, 125.0, layer=pcbnew.F_Fab, size=0.8)

    router = Router(board, footprints)
    # Reserve every fine-pitch escape corridor before global routing so an
    # earlier net cannot occupy a later VSSOP pad's only legal fanout point.
    for reference in ("U3", "U4", "U5"):
        for pad in footprints[reference].Pads():
            router._fanout_point(pad)
    try:
        for net_name in ROUTE_ORDER:
            router.route_net(net_name, pads_by_net[net_name])
    except RuntimeError:
        pcbnew.SaveBoard("/tmp/stage19_route_failure.kicad_pcb", board)
        raise

    ground_smd_pads = [pad for pad in pads_by_net["GND"] if not pad.IsOnLayer(B_CU)]

    add_zone(board, "3V3", F_CU)
    add_zone(board, "GND", B_CU)

    output.parent.mkdir(parents=True, exist_ok=True)
    pcbnew.SaveBoard(str(output), board)
    return {
        "output": str(output),
        "footprints": len(footprints),
        "signal_nets_routed": len(ROUTE_ORDER),
        "ground_smd_pads_routed": len(ground_smd_pads),
        "track_length_mm": round(sum(router.routed_lengths.values()), 3),
        "vias": sum(router.via_counts.values()),
        "per_net_vias": dict(sorted(router.via_counts.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    result = build_board(args.output.resolve())
    for key, value in result.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
