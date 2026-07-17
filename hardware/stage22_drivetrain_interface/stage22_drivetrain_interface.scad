// BB-8 Stage 22 catalog-belt, bearing, keyed-shaft and rail-interface reference.
// REFERENCE CAD ONLY — NOT A FABRICATION RELEASE.
// Fits, GD&T, materials, supplier rating/tension and physical proof remain HOLD.

$fn = 72;
part = is_undef(part) ? "assembly" : part;

plate_l = 140;
plate_w = 68;
plate_t = 6;
wheel_x = 110;
motor_x = 20;
wheel_r = 48;
wheel_w = 26;
shaft_d = 12;
bearing_od = 28;
bearing_w = 8;
pulley_r = 20;
pulley_w = 15;
pulley_z = 33.5;

module rounded_rect_2d(size=[20, 20], radius=3) {
    offset(r=radius) offset(delta=-radius) square(size, center=true);
}

module rail_bracket_2d() {
    difference() {
        translate([plate_l/2, 0]) rounded_rect_2d([plate_l, plate_w], 5);
        for (x=[48, 92], y=[-24, 24])
            translate([x, y]) circle(d=6.6);
        for (x=[12, 128])
            translate([x, 0]) circle(d=6.0);
        translate([wheel_x, 0]) circle(d=28.2);
        translate([motor_x, 0]) circle(d=9.0);
    }
}

module rail_bracket() {
    linear_extrude(height=plate_t, center=true) rail_bracket_2d();
}

module bearing_retainer_2d() {
    difference() {
        circle(d=42);
        circle(d=28.4);
        for (a=[45, 135, 225, 315])
            translate([17.5*cos(a), 17.5*sin(a)]) circle(d=4.5);
    }
}

module bearing_retainer() {
    linear_extrude(height=3, center=true) bearing_retainer_2d();
}

module bearing() {
    difference() {
        cylinder(d=bearing_od, h=bearing_w, center=true);
        cylinder(d=shaft_d, h=bearing_w+2, center=true);
    }
}

module keyed_shaft_envelope() {
    union() {
        cylinder(d=shaft_d, h=82, center=true);
        translate([0, shaft_d/2+1, 21]) cube([4, 2, 20], center=true);
    }
}

module pulley(bore=shaft_d) {
    difference() {
        cylinder(r=pulley_r, h=pulley_w, center=true);
        cylinder(d=bore+0.4, h=pulley_w+2, center=true);
    }
}

module belt_envelope() {
    linear_extrude(height=pulley_w, center=true)
        difference() {
            hull() {
                translate([motor_x, 0]) circle(r=pulley_r+2);
                translate([wheel_x, 0]) circle(r=pulley_r+2);
            }
            hull() {
                translate([motor_x, 0]) circle(r=pulley_r-2);
                translate([wheel_x, 0]) circle(r=pulley_r-2);
            }
        }
}

module assembly() {
    color("silver")
        for (z=[-26, 26])
            translate([0, 0, z]) rail_bracket();
    color([0.08, 0.08, 0.08])
        translate([wheel_x, 0, 0]) cylinder(r=wheel_r, h=wheel_w, center=true);
    color([0.48, 0.50, 0.47])
        translate([motor_x, 0, 0]) cylinder(d=45, h=125.2, center=true);
    color([0.8, 0.8, 0.8])
        translate([wheel_x, 0, 0]) keyed_shaft_envelope();
    color([0.22, 0.22, 0.24])
        for (z=[-19, 19])
            translate([wheel_x, 0, z]) bearing();
    color([0.95, 0.32, 0.07]) {
        translate([motor_x, 0, pulley_z]) pulley(8);
        translate([wheel_x, 0, pulley_z]) pulley(12);
    }
    color([0.08, 0.08, 0.08])
        translate([0, 0, pulley_z]) belt_envelope();
    color([0.15, 0.38, 0.48])
        for (x=[12, 128])
            translate([x, 0, 0]) cylinder(d=6, h=64, center=true);
}

if (part == "rail_bracket") rail_bracket();
else if (part == "rail_bracket_2d") rail_bracket_2d();
else if (part == "bearing_retainer") bearing_retainer();
else if (part == "bearing_retainer_2d") bearing_retainer_2d();
else if (part == "keyed_shaft") keyed_shaft_envelope();
else assembly();
