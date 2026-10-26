/*
 * CoffeeRoast RevD enclosure — OpenSCAD canonical prototype
 *
 * Tool-free rounded tray + snap-on cap. The unmodified PCB drops into a fitted
 * pocket and is retained by four lid hold-down pads. No PCB mounting holes,
 * separate guide rails, screws or cylindrical corner towers are used.
 *
 * PROTOTYPE: USB/cable/Q1/C4/snap dimensions require physical coupons and the
 * manufactured PCBA before mechanical release.
 */

$fn = 64;
part = is_undef(part) ? "assembly" : part;

// Exact functional KiCad board contract plus JLCPCB Y15 production rails.
// The ordered production file is 96 x 70 mm: a 96 x 60 mm functional PCB
// between two 5 mm V-scored process rails. The rails should normally be
// snapped off before installation because they obstruct the edge connectors.
board_variant = is_undef(board_variant) ? "functional" : board_variant;
pcb_x = 96.0;
core_pcb_y = 60.0;
process_rail_y = 5.0;
rails_attached = board_variant == "production_rails_attached";
pcb_y = core_pcb_y + (rails_attached ? 2*process_rail_y : 0);
core_y_offset = rails_attached ? process_rail_y : 0;
pcb_t = 1.6;

// FDM starting values for a calibrated 0.4 mm nozzle.
wall = 1.6;
floor_t = 1.6;
lid_t = 1.6;
pcb_clearance = 0.60;
support_h = 2.8;
clear_above_pcb = 24.0; // PROVISIONAL: measure installed Q1/C4.
corner_r = 3.0;

// PCB retention by enclosure surfaces.
support_size = 5.0;
hold_down_w = 6.0;
hold_down_d = 3.0;
hold_down_gap = 0.20;

// Tool-free snap cap.
snap_clearance = 0.30;
skirt_t = 1.20;
skirt_h = 8.0;
snap_tab_w = 10.0;
snap_tab_h = 1.30;
snap_tab_depth = 0.55;
snap_tab_local_z = -5.60;
snap_relief_w = 0.80;
snap_top_bridge = 0.80;
snap_center_y = (pcb_y + 2*pcb_clearance + 2*wall) / 2;
pry_notch_w = 14.0;
pry_notch_h = 2.5;

// Prototype connector/wire envelopes.
usb_cutout_w = 10.5;
usb_cutout_h = 5.2;
usb_cutout_z_from_board_bottom = 0.2;
field_cutout_h = 7.0;
field_cutout_z_from_board_bottom = 0.4;

// Closed-case passive ventilation, kept away from antenna zone.
vent_w = 2.5;
vent_l = 14.0;
vent_count = 6;
vent_pitch = 5.0;

// Derived dimensions.
inner_x = pcb_x + 2*pcb_clearance;
inner_y = pcb_y + 2*pcb_clearance;
outer_x = inner_x + 2*wall;
outer_y = inner_y + 2*wall;
board_x0 = wall + pcb_clearance;
board_y0 = wall + pcb_clearance;
board_z = floor_t + support_h;
board_top = board_z + pcb_t;
tray_h = board_top + clear_above_pcb;

lid_inner_x = outer_x + 2*snap_clearance;
lid_inner_y = outer_y + 2*snap_clearance;
lid_outer_x = lid_inner_x + 2*skirt_t;
lid_outer_y = lid_inner_y + 2*skirt_t;
lid_x0 = -(snap_clearance + skirt_t);
lid_y0 = -(snap_clearance + skirt_t);
lid_corner_r = corner_r + snap_clearance + skirt_t;

function bx(kx) = board_x0 + kx;
// KiCad coordinates remain referenced to the 96 x 60 mm functional core.
// With production rails attached, the core is shifted 5 mm into the pocket.
function by(ky) = board_y0 + core_y_offset + (core_pcb_y - ky); // Y-down -> Y-up.

eps = 0.05;

module rounded_prism(x, y, z, r) {
    linear_extrude(height=z)
        offset(r=r)
            translate([r, r])
                square([x-2*r, y-2*r]);
}

module tray_support(kx, ky) {
    translate([bx(kx)-support_size/2, by(ky)-support_size/2, floor_t-eps])
        cube([support_size, support_size, support_h+eps]);
}

module tray_shell() {
    rounded_prism(outer_x, outer_y, tray_h, corner_r);
}

module tray_supports() {
    // Isolated underside contacts avoid known THT solder joints.
    tray_support(25.0, 50.0);
    tray_support(25.0, 15.0);
    tray_support(75.0, 30.0);
    tray_support(88.0, 32.0);
}

module tray_cutouts() {
    // PCB pocket. Corner clearance is deliberately rectangular for the PCB.
    translate([wall, wall, floor_t])
        cube([inner_x, inner_y, tray_h-floor_t+2*eps]);

    // USB-C J5 wall, KiCad y=0.
    translate([
        bx(15.0)-usb_cutout_w/2,
        outer_y-wall-eps,
        board_z+usb_cutout_z_from_board_bottom
    ]) cube([usb_cutout_w, wall+2*eps, usb_cutout_h]);

    // Direct-soldered SELV harness openings, KiCad y=60.
    field_slot(5.5, 10.0);   // THERMO
    field_slot(18.0, 10.0);  // SSR
    field_slot(41.62, 20.0); // ESC/AUX
    field_slot(62.0, 10.0);  // FAN
    field_slot(82.0, 10.0);  // 24V IN

    // Two shallow snap pockets on the plain left/right side walls.
    snap_pocket_left();
    snap_pocket_right();
}

module field_slot(kx, width) {
    translate([
        bx(kx)-width/2,
        -eps,
        board_z+field_cutout_z_from_board_bottom
    ]) cube([width, wall+2*eps, field_cutout_h]);
}

module snap_pocket_left() {
    pocket_z = tray_h + snap_tab_local_z - 0.15;
    translate([
        -eps,
        snap_center_y-snap_tab_w/2-0.25,
        pocket_z
    ]) cube([
        snap_tab_depth+0.20,
        snap_tab_w+0.50,
        snap_tab_h+0.30
    ]);
}

module snap_pocket_right() {
    pocket_z = tray_h + snap_tab_local_z - 0.15;
    translate([
        outer_x-snap_tab_depth-0.15,
        snap_center_y-snap_tab_w/2-0.25,
        pocket_z
    ]) cube([
        snap_tab_depth+0.20+eps,
        snap_tab_w+0.50,
        snap_tab_h+0.30
    ]);
}

module tray() {
    union() {
        difference() {
            tray_shell();
            tray_cutouts();
        }
        tray_supports();
    }
}

module lid_plate() {
    translate([lid_x0, lid_y0, 0])
        rounded_prism(lid_outer_x, lid_outer_y, lid_t, lid_corner_r);
}

module lid_skirt() {
    translate([0, 0, -skirt_h])
        difference() {
            translate([lid_x0, lid_y0, 0])
                rounded_prism(lid_outer_x, lid_outer_y, skirt_h+eps, lid_corner_r);
            translate([-snap_clearance, -snap_clearance, -eps])
                rounded_prism(
                    lid_inner_x,
                    lid_inner_y,
                    skirt_h+3*eps,
                    corner_r+snap_clearance
                );
        }
}

module lid_snap_nubs() {
    // Left nub points inward (+X), right nub inward (-X).
    translate([
        -snap_clearance-0.10,
        snap_center_y-snap_tab_w/2,
        snap_tab_local_z
    ]) cube([
        snap_clearance+snap_tab_depth+0.10,
        snap_tab_w,
        snap_tab_h
    ]);

    translate([
        outer_x-snap_tab_depth,
        snap_center_y-snap_tab_w/2,
        snap_tab_local_z
    ]) cube([
        snap_clearance+snap_tab_depth+0.10,
        snap_tab_w,
        snap_tab_h
    ]);
}

module lid_hold_down(kx, ky, sx, sy) {
    post_h = clear_above_pcb - hold_down_gap;
    translate([bx(kx)-sx/2, by(ky)-sy/2, -post_h])
        cube([sx, sy, post_h+0.20]);
}

module lid_hold_downs() {
    lid_hold_down(30.0, 1.5, hold_down_w, hold_down_d);
    lid_hold_down(26.5, 58.5, hold_down_w, hold_down_d);
    lid_hold_down(1.5, 25.0, hold_down_d, hold_down_w);
    lid_hold_down(94.5, 40.0, hold_down_d, hold_down_w);
}

module snap_relief_slots() {
    // Slits isolate two flexible side tabs while leaving a top bridge.
    for (yy = [snap_center_y-snap_tab_w/2, snap_center_y+snap_tab_w/2]) {
        translate([
            lid_x0-eps,
            yy-snap_relief_w/2,
            -skirt_h-eps
        ]) cube([
            skirt_t+2*eps,
            snap_relief_w,
            skirt_h-snap_top_bridge+2*eps
        ]);
        translate([
            outer_x+snap_clearance-eps,
            yy-snap_relief_w/2,
            -skirt_h-eps
        ]) cube([
            skirt_t+2*eps,
            snap_relief_w,
            skirt_h-snap_top_bridge+2*eps
        ]);
    }
}

module pry_notch() {
    // Bottom-edge fingernail notch on the front skirt, away from field openings.
    translate([
        bx(68.0)-pry_notch_w/2,
        lid_y0-eps,
        -skirt_h-eps
    ]) cube([
        pry_notch_w,
        skirt_t+2*eps,
        pry_notch_h
    ]);
}

module lid_function_cutouts() {
    // SW1 RESET and SW2 BOOT access holes.
    for (p = [[42.0,27.0], [46.0,36.0]])
        translate([bx(p[0]), by(p[1]), -eps])
            cylinder(h=lid_t+2*eps, r=2.0);

    // Q1/buck/L1 vents, outside ESP32 antenna keepout.
    vent_y = by(43.0);
    for (i = [0:vent_count-1])
        translate([
            bx(52.0)+i*vent_pitch,
            vent_y-vent_l/2,
            -eps
        ]) cube([vent_w, vent_l, lid_t+2*eps]);

    snap_relief_slots();
    pry_notch();
}

module lid() {
    difference() {
        union() {
            lid_plate();
            lid_skirt();
            lid_snap_nubs();
            lid_hold_downs();
        }
        lid_function_cutouts();
    }
}

module lid_print() {
    // Outer face on the print bed; skirt and hold-down pads grow upward.
    translate([0, outer_y, lid_t])
        rotate([180, 0, 0])
            lid();
}

module pcb_proxy() {
    color([0.03, 0.55, 0.18]) {
        translate([board_x0, board_y0, board_z])
            cube([pcb_x, pcb_y, pcb_t]);
        // J5 USB-C provisional body.
        translate([bx(15.0)-4.5, by(3.675)-3.7, board_top])
            cube([9.0, 7.4, 3.3]);
        // Q1 vertical TO-220 provisional body.
        translate([bx(56.54)-5.25, by(47.0)-2.4, board_top+3.0])
            cube([10.5, 4.8, 16.0]);
        // C4 provisional radial capacitor.
        translate([bx(66.5), by(46.5), board_top])
            cylinder(h=16.0, r=4.0);
        // ESP32 module proxy.
        translate([bx(72.0)-9.0, by(15.9)-12.75, board_top])
            cube([18.0, 25.5, 3.2]);
        // L1 proxy.
        translate([bx(89.0)-3.1, by(41.0)-3.1, board_top])
            cube([6.2, 6.2, 4.8]);
        for (p = [[42.0,27.0], [46.0,36.0]])
            translate([bx(p[0])-3.0, by(p[1])-3.0, board_top])
                cube([6.0, 6.0, 3.6]);
    }
}

module closed_assembly() {
    color([0.56, 0.62, 0.70]) tray();
    pcb_proxy();
    color([0.12, 0.36, 0.72])
        translate([0, 0, tray_h]) lid();
}

module exploded_assembly() {
    color([0.56, 0.62, 0.70]) tray();
    pcb_proxy();
    color([0.12, 0.36, 0.72])
        translate([112, 0, tray_h+2]) lid();
}

if (part == "tray") {
    tray();
} else if (part == "lid") {
    lid();
} else if (part == "lid_print") {
    lid_print();
} else if (part == "board_proxy") {
    pcb_proxy();
} else if (part == "closed") {
    closed_assembly();
} else if (part == "exploded") {
    exploded_assembly();
} else {
    closed_assembly();
}
