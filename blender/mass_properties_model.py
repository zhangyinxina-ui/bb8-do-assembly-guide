"""Pure-Python mass, centre-of-mass and inertia model for BB-8 stage 14."""

from __future__ import annotations

import itertools
import math


CONFIG = {
    "status": "DESIGN_ASSUMPTIONS_REPLACE_WITH_MEASURED_MASSES",
    "body_radius_m": 0.254,
    "target_accel_mps2": 0.70,
    "target_speed_mps": 1.0,
    "minimum_nominal_com_offset_m": 0.050,
    "minimum_worst_case_com_offset_m": 0.020,
    "legacy_unverified_com_offset_m": 0.110,
    "additional_ballast_position_z_m": -0.220,
    "drive_wheel_radius_m": 0.048,
    "motor_count": 2,
    "motor_continuous_torque_nm": 0.6,
    "required_design_safety_factor": 2.0,
    "drive_efficiency": 0.72,
    "rolling_resistance_coefficient": 0.03,
    "shell_rotating_mass_kg": 1.2,
}


def component(component, object_name, masses, position, dimensions, source, shape="box"):
    return {
        "component": component,
        "object_name": object_name,
        "mass_min_kg": masses[0],
        "mass_nominal_kg": masses[1],
        "mass_max_kg": masses[2],
        "position_m": list(position),
        "dimensions_m": list(dimensions),
        "shape": shape,
        "source": source,
        "physical_test_status": "NOT_RUN",
    }


COMPONENTS = [
    component("rotating shell and exterior panels", "BB-8 body shell - 508 mm", (0.90, 1.20, 1.60),
              (0, 0, 0), (0.508, 0.508, 0.508), "community full-size shell mass assumption", "thin_sphere"),
    component("complete head including follower hardware", "Head dome - 295 mm", (0.55, 0.65, 0.80),
              (0, 0, 0.320), (0.295, 0.295, 0.197), "stage-physics head mass assumption"),
    component("4S battery pack", "Internal 4S battery ballast", (1.00, 1.20, 1.50),
              (0, 0.005, -0.078), (0.120, 0.074, 0.056), "candidate battery envelope; pack not purchased"),
    component("left geared motor", "Internal geared motor L", (0.360, 0.609, 0.609),
              (-0.0724, 0, -0.135), (0.1252, 0.045, 0.045), "vendor conflict: drawing 360 g / product page 609 g"),
    component("right geared motor", "Internal geared motor R", (0.360, 0.609, 0.609),
              (0.0724, 0, -0.135), (0.1252, 0.045, 0.045), "vendor conflict: drawing 360 g / product page 609 g"),
    component("left drive wheel", "Internal drive wheel L", (0.12, 0.18, 0.25),
              (-0.155, 0, -0.135), (0.026, 0.096, 0.096), "96 mm wheel mass assumption"),
    component("right drive wheel", "Internal drive wheel R", (0.12, 0.18, 0.25),
              (0.155, 0, -0.135), (0.026, 0.096, 0.096), "96 mm wheel mass assumption"),
    component("left hub shaft and fasteners", "Internal 8 mm key hub L", (0.08, 0.11, 0.15),
              (-0.148, 0, -0.135), (0.040, 0.026, 0.026), "hub/shaft/fastener grouped assumption"),
    component("right hub shaft and fasteners", "Internal 8 mm key hub R", (0.08, 0.11, 0.15),
              (0.148, 0, -0.135), (0.040, 0.026, 0.026), "hub/shaft/fastener grouped assumption"),
    component("chassis rails mounts and crossmember", "Internal aluminium chassis", (0.40, 0.55, 0.75),
              (0, 0, -0.120), (0.380, 0.120, 0.052), "6061 geometry plus grouped mounting hardware"),
    component("electronics tray controller and current boards", "Internal electronics tray", (0.20, 0.32, 0.50),
              (0, 0.010, -0.098), (0.104, 0.080, 0.024), "PCB and tray grouped assumption"),
    component("fuse contactor and main connector", "Internal fuse and contactor", (0.10, 0.15, 0.22),
              (0.105, 0.020, -0.095), (0.044, 0.028, 0.024), "power switching grouped assumption"),
    component("mast braces and lower carrier", "Internal magnetic mast", (0.30, 0.45, 0.65),
              (0, 0, 0.075), (0.180, 0.120, 0.340), "mast and brace grouped assumption"),
    component("six chassis-side magnets", "Internal chassis magnet 1", (0.075, 0.085, 0.110),
              (0, 0, 0.247), (0.090, 0.090, 0.006), "NdFeB density envelope for six 20x6 mm magnets"),
    component("stabiliser rollers and arms", "Internal stabiliser roller L F", (0.18, 0.26, 0.38),
              (0, 0, 0.100), (0.220, 0.180, 0.220), "four rollers and arms grouped assumption"),
    component("straps wiring latches and omitted small hardware", "Internal battery strap front", (0.20, 0.30, 0.45),
              (0, 0, -0.030), (0.400, 0.400, 0.030), "explicit residual-mass allowance"),
    component("sealed low ballast cassette", "Internal sealed low ballast cassette", (1.35, 1.50, 1.65),
              (0, 0, -0.205), (0.120, 0.070, 0.024), "steel volume and sealed-cassette allowance"),
]


def default_input():
    return {"config": dict(CONFIG), "components": [dict(item) for item in COMPONENTS]}


def _intrinsic_inertia(component_data, mass):
    dx, dy, dz = component_data["dimensions_m"]
    if component_data["shape"] == "thin_sphere":
        radius = dx / 2
        value = (2 / 3) * mass * radius * radius
        return value, value, value
    return (
        mass * (dy * dy + dz * dz) / 12,
        mass * (dx * dx + dz * dz) / 12,
        mass * (dx * dx + dy * dy) / 12,
    )


def evaluate(components, masses):
    total = sum(masses)
    com = [sum(m * c["position_m"][axis] for c, m in zip(components, masses)) / total for axis in range(3)]
    inertia = [0.0, 0.0, 0.0]
    for c, mass in zip(components, masses):
        intrinsic = _intrinsic_inertia(c, mass)
        dx, dy, dz = (c["position_m"][i] - com[i] for i in range(3))
        inertia[0] += intrinsic[0] + mass * (dy * dy + dz * dz)
        inertia[1] += intrinsic[1] + mass * (dx * dx + dz * dz)
        inertia[2] += intrinsic[2] + mass * (dx * dx + dy * dy)
    return {"total_mass_kg": total, "com_m": com, "inertia_com_kg_m2": inertia}


def _extreme_com(components, axis, minimize):
    best_value = math.inf if minimize else -math.inf
    best_masses = None
    for choices in itertools.product((0, 1), repeat=len(components)):
        masses = [c["mass_min_kg"] if choice == 0 else c["mass_max_kg"] for c, choice in zip(components, choices)]
        total = sum(masses)
        value = sum(m * c["position_m"][axis] for c, m in zip(components, masses)) / total
        if (minimize and value < best_value) or (not minimize and value > best_value):
            best_value = value
            best_masses = masses
    return evaluate(components, best_masses)


def summarize(model_input):
    config = model_input["config"]
    components = model_input["components"]
    nominal = evaluate(components, [c["mass_nominal_kg"] for c in components])
    minimum_mass = evaluate(components, [c["mass_min_kg"] for c in components])
    maximum_mass = evaluate(components, [c["mass_max_kg"] for c in components])
    lowest_com = _extreme_com(components, 2, True)
    highest_com = _extreme_com(components, 2, False)
    g = 9.80665
    offset = -nominal["com_m"][2]
    worst_offset = -highest_com["com_m"][2]
    torque_10 = nominal["total_mass_kg"] * g * offset * math.sin(math.radians(10))
    pitch_period = 2 * math.pi * math.sqrt(nominal["inertia_com_kg_m2"][1] /
                                           (nominal["total_mass_kg"] * g * offset))
    force_limit = (config["motor_continuous_torque_nm"] / config["required_design_safety_factor"] *
                   config["motor_count"] * config["drive_efficiency"] / config["drive_wheel_radius_m"])
    rolling_force = config["rolling_resistance_coefficient"] * nominal["total_mass_kg"] * g
    effective_mass = nominal["total_mass_kg"] + 2 * config["shell_rotating_mass_kg"] / 3
    max_accel = max(0.0, (force_limit - rolling_force) / effective_mass)
    target_z = -config["legacy_unverified_com_offset_m"]
    ballast_z = config["additional_ballast_position_z_m"]
    additional_ballast = (nominal["total_mass_kg"] * (target_z - nominal["com_m"][2]) /
                          (ballast_z - target_z))
    checks = {
        "nominal_com_offset": offset >= config["minimum_nominal_com_offset_m"],
        "worst_case_com_offset": worst_offset >= config["minimum_worst_case_com_offset_m"],
        "continuous_torque_derated_acceleration": max_accel >= config["target_accel_mps2"],
    }
    return {
        "status": "PASS_WITH_MASS_AND_ACCELERATION_DERATING" if all(checks.values()) else "HOLD",
        "nominal": nominal,
        "minimum_mass": minimum_mass,
        "maximum_mass": maximum_mass,
        "lowest_com": lowest_com,
        "highest_com": highest_com,
        "nominal_com_offset_below_center_m": offset,
        "worst_case_com_offset_below_center_m": worst_offset,
        "restoring_torque_10deg_nm": torque_10,
        "pitch_natural_period_s": pitch_period,
        "target_equilibrium_lean_deg": math.degrees(math.atan2(config["target_accel_mps2"], g)),
        "max_accel_for_2x_continuous_torque_mps2": max_accel,
        "additional_ballast_for_legacy_110mm_kg": additional_ballast,
        "checks": checks,
    }
