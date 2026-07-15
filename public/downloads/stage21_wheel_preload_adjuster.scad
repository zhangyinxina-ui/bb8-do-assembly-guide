// BB-8 Stage 21 tangent-axis wheel-preload cassette.
// REFERENCE CAD ONLY — NOT A FABRICATION RELEASE.
// Hole fits, material, fastener preload, belt rating and physical contact remain HOLD.

$fn = 72;

part = is_undef(part) ? "assembly" : part;
travel = is_undef(travel) ? 3 : travel; // 0..12 mm from inner stop; 3 mm is nominal contact.
show_shell = is_undef(show_shell) ? false : show_shell;

shell_r = 254;
wheel_r = 48;
wheel_half_width = 13;
crown_drop = 0.75;
plate_l = 132;
plate_w = 64;
plate_t = 6;
wheel_x = 110;
motor_x = 30;
axis_spacing = wheel_x - motor_x;
moving_plate_z = 19;
fixed_plate_z = 26;
slot_w = 6.6;
slot_l = 18.6;
nominal_travel = 3;
delta = travel - nominal_travel;
pulley_pitch_r = 24 * 5 / (2 * PI);
pulley_visual_r = 20;
pulley_w = 15;
pulley_z = fixed_plate_z + plate_t / 2 + pulley_w / 2 + 2;
neutral_center_r = 206;
base_origin_r = neutral_center_r - wheel_x;
nx = 155 / 206;
nz = -sqrt(1 - nx * nx);

module rounded_rect_2d(size=[20, 20], radius=3) {
    offset(r=radius) offset(delta=-radius) square(size, center=true);
}

module slot_2d(length=slot_l, width=slot_w) {
    hull() {
        translate([-(length-width)/2, 0]) circle(d=width);
        translate([(length-width)/2, 0]) circle(d=width);
    }
}

module fixed_plate_2d() {
    difference() {
        translate([plate_l/2, 0]) rounded_rect_2d([plate_l, plate_w], 5);
        // Slot centre is 3 mm outward of nominal so travel spans -3..+9 mm.
        for (x=[48, 84], y=[-23, 23])
            translate([x + 3, y]) slot_2d();
        for (x=[10, 122], y=[-24, 24])
            translate([x, y]) circle(d=6.6);
    }
}

module moving_plate_2d() {
    difference() {
        translate([plate_l/2, 0]) rounded_rect_2d([plate_l, plate_w], 5);
        translate([wheel_x, 0]) circle(d=28.2); // 6001-2RS envelope; fit not released.
        translate([motor_x, 0]) circle(d=9.0);
        for (a=[45, 135, 225, 315])
            translate([motor_x + 17.5*cos(a), 17.5*sin(a)]) circle(d=4.5);
        for (x=[48, 84], y=[-23, 23])
            translate([x, y]) circle(d=6.6);
        for (x=[12, 120], y=[-24, 24])
            translate([x, y]) circle(d=5.2);
    }
}

module fixed_plate() {
    linear_extrude(height=plate_t, center=true) fixed_plate_2d();
}

module moving_plate() {
    linear_extrude(height=plate_t, center=true) moving_plate_2d();
}

module crowned_wheel() {
    points = concat(
        [[0, -wheel_half_width]],
        [for (i=[0:24])
            let(s=-wheel_half_width + 2*wheel_half_width*i/24,
                r=wheel_r - crown_drop*pow(s/wheel_half_width, 2))
            [r, s]],
        [[0, wheel_half_width]]
    );
    rotate_extrude(convexity=10) polygon(points);
}

module pulley(bore=8) {
    difference() {
        cylinder(r=pulley_visual_r, h=pulley_w, center=true);
        cylinder(d=bore + 0.4, h=pulley_w + 2, center=true);
    }
}

module belt_envelope() {
    linear_extrude(height=pulley_w, center=true)
        difference() {
            hull() {
                translate([motor_x, 0]) circle(r=pulley_visual_r + 2);
                translate([wheel_x, 0]) circle(r=pulley_visual_r + 2);
            }
            hull() {
                translate([motor_x, 0]) circle(r=pulley_visual_r - 2);
                translate([wheel_x, 0]) circle(r=pulley_visual_r - 2);
            }
        }
}

module motor_envelope() {
    cylinder(d=45, h=125.2, center=true);
}

module wheel_shaft() {
    cylinder(d=12, h=58, center=true);
}

module bearing() {
    difference() {
        cylinder(d=28, h=8, center=true);
        cylinder(d=12, h=10, center=true);
    }
}

module jackscrew_block() {
    difference() {
        translate([-8, 0, 0]) cube([16, 24, 18], center=true);
        rotate([0, 90, 0]) cylinder(d=5.2, h=20, center=true);
    }
}

module jackscrew() {
    rotate([0, 90, 0]) cylinder(d=6, h=42, center=true);
}

module hard_stop_pair() {
    for (y=[-27, 27]) {
        translate([-1, y, 0]) cube([6, 8, 18], center=true);
        translate([plate_l+1, y, 0]) cube([6, 8, 18], center=true);
    }
}

module clamp_bolts() {
    for (x=[48, 84], y=[-23, 23])
        translate([x + delta, y, 0]) cylinder(d=6, h=64, center=true);
}

module cassette() {
    color("silver")
        for (z=[-fixed_plate_z, fixed_plate_z])
            translate([0, 0, z]) fixed_plate();
    color([0.95, 0.32, 0.07])
        for (z=[-moving_plate_z, moving_plate_z])
            translate([delta, 0, z]) moving_plate();
    color([0.08, 0.08, 0.08])
        translate([wheel_x + delta, 0, 0]) crowned_wheel();
    color([0.45, 0.47, 0.45])
        translate([motor_x + delta, 0, 0]) motor_envelope();
    color([0.75, 0.75, 0.75])
        translate([wheel_x + delta, 0, 0]) wheel_shaft();
    color([0.25, 0.25, 0.28])
        for (z=[-moving_plate_z, moving_plate_z])
            translate([wheel_x + delta, 0, z]) bearing();
    color([0.95, 0.32, 0.07]) {
        translate([motor_x + delta, 0, pulley_z]) pulley(8);
        translate([wheel_x + delta, 0, pulley_z]) pulley(12);
    }
    color([0.08, 0.08, 0.08])
        translate([delta, 0, pulley_z]) belt_envelope();
    color([0.25, 0.25, 0.25]) {
        clamp_bolts();
        translate([-16 + travel/2, 0, 0]) jackscrew();
    }
    color([0.95, 0.32, 0.07]) jackscrew_block();
    color([0.25, 0.25, 0.25]) hard_stop_pair();
}

module right_local_to_global() {
    multmatrix([
        [nx, 0, -nz, base_origin_r*nx],
        [0, 1, 0, 0],
        [nz, 0, nx, base_origin_r*nz],
        [0, 0, 0, 1]
    ]) children();
}

module left_local_to_global() {
    multmatrix([
        [-nx, 0, -nz, -base_origin_r*nx],
        [0, 1, 0, 0],
        [nz, 0, -nx, base_origin_r*nz],
        [0, 0, 0, 1]
    ]) children();
}

module global_pair() {
    right_local_to_global() cassette();
    left_local_to_global() cassette();
    if (show_shell)
        color([0.82, 0.86, 0.90, 0.16])
            difference() {
                sphere(r=shell_r + 1);
                sphere(r=shell_r - 1);
                translate([0, -320, 0]) cube([640, 640, 640], center=true);
            }
}

if (part == "fixed_plate") fixed_plate();
else if (part == "moving_plate") moving_plate();
else if (part == "fixed_plate_2d") fixed_plate_2d();
else if (part == "moving_plate_2d") moving_plate_2d();
else if (part == "jackscrew_block") jackscrew_block();
else if (part == "crowned_wheel") crowned_wheel();
else if (part == "global_pair") global_pair();
else cassette();
