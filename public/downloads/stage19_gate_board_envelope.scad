// Stage 19 pre-CAD mechanical envelope only.
// No copper, footprint, creepage, DRC or fabrication release is implied.

$fn = 48;

board_x = 50;
board_y = 35;
board_z = 1.6;
hole_d = 3.2;
holes = [[3, 3], [47, 3], [3, 32], [47, 32]];

module rounded_board() {
  difference() {
    linear_extrude(board_z)
      offset(r = 1.5)
        offset(delta = -1.5)
          square([board_x, board_y]);
    for (p = holes)
      translate([p[0], p[1], -0.1]) cylinder(d = hole_d, h = board_z + 0.2);
  }
}

module block(x, y, sx, sy, sz, label_kind = 0) {
  translate([x - sx / 2, y - sy / 2, board_z]) cube([sx, sy, sz]);
}

color([0.03, 0.28, 0.16]) rounded_board();

// JST XH top-entry connector envelopes; 9.8 mm mounting height above PCB.
color([0.92, 0.92, 0.82]) {
  block(8, 7, 7.4, 5.75, 9.8);   // J1 B2B-XH-A
  block(25, 7, 17.4, 5.75, 9.8); // J2 B6B-XH-A
  block(39, 28, 14.9, 5.75, 9.8); // J3 B5B-XH-A
  block(8, 28, 7.4, 5.75, 9.8);  // J4 B2B-XH-A
  block(18, 28, 7.4, 5.75, 9.8); // J5 B2B-XH-A
}

// Optocoupler and logic-package placement envelopes.
color([0.12, 0.12, 0.14]) {
  block(9, 17, 7.62, 4.6, 4.0); // U1 VO617A-4
  block(9, 22, 7.62, 4.6, 4.0); // U2 VO617A-4
  block(25, 17, 3.2, 3.2, 1.2); // U3 VSSOP-8
  block(32, 17, 3.2, 3.2, 1.2); // U4 VSSOP-8
  block(39, 17, 3.2, 3.2, 1.2); // U5 VSSOP-8
}

// Two 0.5 W input resistors and test-point corridor.
color([0.72, 0.42, 0.12]) {
  block(17, 16, 6.5, 2.5, 2.5);
  block(17, 21, 6.5, 2.5, 2.5);
}
color([0.8, 0.65, 0.1]) {
  for (x = [22, 26.5, 31, 35.5, 40, 44.5]) block(x, 23, 1.5, 1.5, 2.0);
}
