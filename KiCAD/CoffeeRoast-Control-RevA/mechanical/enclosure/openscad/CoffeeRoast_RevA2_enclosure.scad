/*
 * CoffeeRoast RevA.2 enclosure — OpenSCAD canonical prototype
 *
 * Rounded tray + snap cap for the ordered 160 x 100 mm functional PCB after
 * removing JLCPCB's two 5 mm V-scored PCBA process rails.
 *
 * PROTOTYPE: cable envelopes, Q1/C4 installed heights, snap fit and thermal
 * behavior require physical validation with the manufactured PCBA.
 */

$fn = 64;
part = is_undef(part) ? "closed" : part;

// Ordered board contract after removing the JLCPCB process rails.
pcb_x = 160.0;
pcb_y = 100.0;
pcb_t = 1.6;

// FDM starting values for a calibrated 0.4 mm nozzle.
wall = 1.6;
floor_t = 1.6;
lid_t = 1.6;
pcb_clearance = 0.60;
support_h = 2.8;
clear_above_pcb = 27.0; // PROVISIONAL: measure installed Q1 and C4.
corner_r = 4.0;

support_size = 5.0;
hold_down_gap = 0.25;

// Tool-free cap; two snap pairs distribute retention along the 160 mm body.
snap_clearance = 0.30;
skirt_t = 1.20;
skirt_h = 8.0;
snap_tab_w = 10.0;
snap_tab_h = 1.30;
snap_tab_depth = 0.55;
snap_tab_local_z = -5.60;
snap_relief_w = 0.80;
snap_top_bridge = 0.80;
snap_centers_y = [15.0, 95.0];
pry_notch_w = 16.0;
pry_notch_h = 2.5;

// Connector and direct-soldered harness envelopes.
usb_cutout_w = 11.0;   // extent along the right wall (Y)
usb_cutout_h = 5.5;
usb_cutout_z_from_board_bottom = 0.2;
field_cutout_h = 11.0;
field_cutout_z_from_board_bottom = 0.3;

// Power-stage ventilation kept left of the ESP32 antenna region.
vent_w = 2.8;
vent_l = 20.0;
vent_count = 8;
vent_pitch = 5.5;

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
function by(ky) = board_y0 + (pcb_y - ky); // KiCad Y-down -> model Y-up.
eps = 0.05;

module rounded_prism(x, y, z, r) {
    linear_extrude(height=z)
        offset(r=r)
            translate([r, r]) square([x-2*r, y-2*r]);
}

module tray_support(kx, ky) {
    translate([bx(kx)-support_size/2, by(ky)-support_size/2, floor_t-eps])
        cube([support_size, support_size, support_h+eps]);
}

module tray_supports() {
    // Isolated underside contacts chosen from anchor-clear board zones. They
    // deliberately avoid the six exposed corner fiducials and known THT joints.
    for (p = [[24,6], [136,6], [6,94], [154,80]]) tray_support(p[0], p[1]);
}

module side_slot(side, ky, width) {
    yy = by(ky)-width/2;
    xx = side == "left" ? -eps : outer_x-wall-eps;
    translate([xx, yy, board_z+field_cutout_z_from_board_bottom])
        cube([wall+2*eps, width, field_cutout_h]);
}

module front_slot(kx, width) {
    translate([bx(kx)-width/2, -eps, board_z+field_cutout_z_from_board_bottom])
        cube([width, wall+2*eps, field_cutout_h]);
}

module snap_pocket(side, yy) {
    pocket_z = tray_h + snap_tab_local_z - 0.15;
    xx = side == "left" ? -eps : outer_x-snap_tab_depth-0.15;
    translate([xx, yy-snap_tab_w/2-0.25, pocket_z])
        cube([snap_tab_depth+0.20+eps, snap_tab_w+0.50, snap_tab_h+0.30]);
}

module tray_cutouts() {
    // Rectangular PCB pocket.
    translate([wall, wall, floor_t])
        cube([inner_x, inner_y, tray_h-floor_t+2*eps]);

    // Left wall: J1 24V input and J2 fan harness.
    side_slot("left", 18.0, 13.0);
    side_slot("left", 48.0, 13.0);

    // Right wall: J3 SSR, J4 thermocouple and J5 USB-C.
    side_slot("right", 70.0, 13.0);
    side_slot("right", 52.0, 13.0);
    translate([outer_x-wall-eps, by(31.0)-usb_cutout_w/2,
               board_z+usb_cutout_z_from_board_bottom])
        cube([wall+2*eps, usb_cutout_w, usb_cutout_h]);

    // Front wall: J6 ESC four-wire harness near KiCad y=100.
    front_slot(128.0, 20.0);

    for (yy = snap_centers_y) {
        snap_pocket("left", yy);
        snap_pocket("right", yy);
    }
}

module tray() {
    union() {
        difference() {
            rounded_prism(outer_x, outer_y, tray_h, corner_r);
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
    translate([0,0,-skirt_h]) difference() {
        translate([lid_x0,lid_y0,0])
            rounded_prism(lid_outer_x,lid_outer_y,skirt_h+eps,lid_corner_r);
        translate([-snap_clearance,-snap_clearance,-eps])
            rounded_prism(lid_inner_x,lid_inner_y,skirt_h+3*eps,
                          corner_r+snap_clearance);
    }
}

module lid_snap_nubs() {
    for (yy = snap_centers_y) {
        translate([-snap_clearance-0.10, yy-snap_tab_w/2, snap_tab_local_z])
            cube([snap_clearance+snap_tab_depth+0.10,snap_tab_w,snap_tab_h]);
        translate([outer_x-snap_tab_depth, yy-snap_tab_w/2, snap_tab_local_z])
            cube([snap_clearance+snap_tab_depth+0.10,snap_tab_w,snap_tab_h]);
    }
}

module lid_hold_down(kx, ky, sx, sy) {
    post_h = clear_above_pcb-hold_down_gap;
    translate([bx(kx)-sx/2,by(ky)-sy/2,-post_h])
        cube([sx,sy,post_h+0.20]);
}

module lid_hold_downs() {
    // Bare-edge locations selected from the ordered RevA.2 layout.
    lid_hold_down(20,2,7,3);
    lid_hold_down(140,2,7,3);
    lid_hold_down(20,98,7,3);
    lid_hold_down(80,98,7,3);
    lid_hold_down(2,70,3,7);
    lid_hold_down(158,85,3,7);
}

module snap_relief_slots() {
    for (center = snap_centers_y)
        for (yy = [center-snap_tab_w/2, center+snap_tab_w/2]) {
            translate([lid_x0-eps,yy-snap_relief_w/2,-skirt_h-eps])
                cube([skirt_t+2*eps,snap_relief_w,
                      skirt_h-snap_top_bridge+2*eps]);
            translate([outer_x+snap_clearance-eps,yy-snap_relief_w/2,
                       -skirt_h-eps])
                cube([skirt_t+2*eps,snap_relief_w,
                      skirt_h-snap_top_bridge+2*eps]);
        }
}

module lid_function_cutouts() {
    // RESET SW1 and BOOT SW2.
    for (p = [[50,8],[28,28]])
        translate([bx(p[0]),by(p[1]),-eps])
            cylinder(h=lid_t+2*eps,r=2.2);

    // Q1/U4/L1 power-stage vents, away from U1 antenna region.
    vent_y = by(69.0);
    for (i=[0:vent_count-1])
        translate([bx(24.0)+i*vent_pitch,vent_y-vent_l/2,-eps])
            cube([vent_w,vent_l,lid_t+2*eps]);

    snap_relief_slots();
    translate([bx(80)-pry_notch_w/2,lid_y0-eps,-skirt_h-eps])
        cube([pry_notch_w,skirt_t+2*eps,pry_notch_h]);
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
    translate([0,outer_y,lid_t]) rotate([180,0,0]) lid();
}

module pcb_proxy() {
    color([0.03,0.55,0.18]) {
        translate([board_x0,board_y0,board_z]) cube([pcb_x,pcb_y,pcb_t]);
        // J5 USB-C body at the right edge.
        translate([bx(156.325)-3.7,by(31)-4.5,board_top])
            cube([7.4,9.0,3.3]);
        // Q1 vertical TO-220 and C4 radial capacitor — provisional envelopes.
        translate([bx(42.46)-5.25,by(58)-2.4,board_top+3])
            cube([10.5,4.8,18]);
        translate([bx(7.46),by(23.2),board_top]) cylinder(h=16,r=4.2);
        // ESP32 module and power inductor proxies.
        translate([bx(85)-9,by(28)-12.75,board_top]) cube([18,25.5,3.2]);
        translate([bx(45.5)-3.2,by(76.1)-3.2,board_top]) cube([6.4,6.4,4.8]);
        for (p=[[50,8],[28,28]])
            translate([bx(p[0])-3,by(p[1])-3,board_top]) cube([6,6,3.6]);
    }
}

module closed_assembly() {
    color([0.56,0.62,0.70]) tray();
    pcb_proxy();
    color([0.12,0.36,0.72]) translate([0,0,tray_h]) lid();
}

module exploded_assembly() {
    color([0.56,0.62,0.70]) tray();
    pcb_proxy();
    color([0.12,0.36,0.72]) translate([178,0,tray_h+2]) lid();
}

if (part=="tray") tray();
else if (part=="lid") lid();
else if (part=="lid_print") lid_print();
else if (part=="board_proxy") pcb_proxy();
else if (part=="exploded") exploded_assembly();
else closed_assembly();
