/*
 * CoffeeRoast RevA.2 + Mean Well LOP-200-24 stacked enclosure
 *
 * Three printed parts:
 *   lower_base      tool-closed, touch-protected PSU chamber
 *   controller_deck solid separator + drop-in controller tray
 *   lid_print       snap cap for the SELV controller chamber
 *
 * Compact footprint: the 160 x 100 mm controller defines XY. The open-frame
 * 230 V PSU is below it, never exposed when only the snap lid is removed.
 *
 * SAFETY PROTOTYPE ONLY. A printed shell is not certification. Final use needs
 * UL94-V-0 material, conductive PSU pillars/PE bonding, certified cable gland,
 * touch-probe/creepage/clearance review and worst-case thermal testing.
 */

$fn = 64;
part = is_undef(part) ? "closed" : part;
eps = 0.05;

// Manufactured controller board after removing both process rails.
pcb_x = 160.0;
pcb_y = 100.0;
pcb_t = 1.6;
pcb_clearance = 0.60;

// Exact Mean Well LOP-200-24 contract.
psu_x = 101.6;
psu_y = 50.8;
psu_h = 25.4;
psu_hole_dx = 95.25;
psu_hole_dy = 44.45;
psu_hole_offset = 3.175;
psu_hole_d = 3.3;
psu_standoff_h = 6.0; // physical conductive M3 pillars, max Ø6 mm

// Printed shell, calibrated 0.4 mm nozzle starting values.
wall = 2.4;
floor_t = 2.4;
separator_t = 2.4;
lid_t = 1.8;
corner_r = 4.0;

inner_x = pcb_x + 2*pcb_clearance;
inner_y = pcb_y + 2*pcb_clearance;
outer_x = inner_x + 2*wall;
outer_y = inner_y + 2*wall;
board_x0 = wall + pcb_clearance;
board_y0 = wall + pcb_clearance;

// Lower, tool-closed PSU chamber.
psu_side_clear = 7.0;
psu_clear_above = 7.0;
lower_h = floor_t + psu_standoff_h + psu_h + psu_clear_above;
psu_x0 = (outer_x-psu_x)/2;
psu_y0 = (outer_y-psu_y)/2;
psu_z0 = floor_t + psu_standoff_h;
ac_gland_d = 16.2;
ac_gland_z = 20.0;
ac_gland_y = outer_y/2;

// Four screws lock the solid controller deck to the PSU chamber. Their heads
// remain below the controller PCB, which is installed afterwards.
deck_screw_xy = [[9,9],[outer_x-9,9],[9,outer_y-9],[outer_x-9,outer_y-9]];
base_boss_d = 8.0;
deck_screw_d = 3.4;
base_insert_d = 4.2;
base_insert_depth = 7.0;

// Upper SELV controller tray.
support_h = 3.0;
clear_above_pcb = 27.0; // provisional: measure installed Q1/C4
board_z_local = separator_t + support_h;
board_top_local = board_z_local + pcb_t;
upper_h = board_top_local + clear_above_pcb;
support_size = 5.0;
hold_down_gap = 0.25;

// Snap lid.
snap_clearance = 0.30;
skirt_t = 1.20;
skirt_h = 8.0;
snap_tab_w = 10.0;
snap_tab_h = 1.30;
snap_tab_depth = 0.55;
snap_tab_local_z = -5.60;
snap_centers_y = [18.0, outer_y-18.0];
snap_relief_w = 0.80;
snap_top_bridge = 0.80;
pry_notch_w = 16.0;
pry_notch_h = 2.5;

// Connector openings copied from the verified RevA.2 mechanical map.
usb_cutout_w = 11.0;
usb_cutout_h = 5.8;
field_cutout_h = 11.0;

// Narrow ventilation slots; final touch-probe and thermal tests remain gates.
vent_slot_w = 2.0;
vent_slot_l = 25.0;
vent_pitch = 6.0;

function bx(kx) = board_x0 + kx;
function by(ky) = board_y0 + (pcb_y-ky); // KiCad Y-down -> model Y-up
function psu_hole_x(ix) = psu_x0 + psu_hole_offset + ix*psu_hole_dx;
function psu_hole_y(iy) = psu_y0 + psu_hole_offset + iy*psu_hole_dy;

module rounded_prism(x,y,z,r) {
    linear_extrude(height=z)
        offset(r=r) translate([r,r]) square([x-2*r,y-2*r]);
}

module lower_bosses() {
    for (p=deck_screw_xy)
        translate([p[0],p[1],floor_t-eps]) cylinder(h=lower_h-floor_t+eps,d=base_boss_d);
}

module lower_base() {
    difference() {
        union() {
            difference() {
                rounded_prism(outer_x,outer_y,lower_h,corner_r);
                translate([wall,wall,floor_t])
                    rounded_prism(outer_x-2*wall,outer_y-2*wall,lower_h-floor_t+2*eps,
                                  max(0.8,corner_r-wall));
            }
            lower_bosses();
        }

        // Mean Well mounting holes and shallow external screw-head recesses.
        for (ix=[0:1],iy=[0:1]) {
            translate([psu_hole_x(ix),psu_hole_y(iy),-eps])
                cylinder(h=floor_t+2*eps,d=3.4);
            translate([psu_hole_x(ix),psu_hole_y(iy),-eps])
                cylinder(h=1.0+eps,d=6.4);
        }

        // Heat-set inserts for the controller deck, loaded from the open top.
        for (p=deck_screw_xy)
            translate([p[0],p[1],lower_h-base_insert_depth])
                cylinder(h=base_insert_depth+eps,d=base_insert_d);

        // Certified AC cable gland. No external opening exists on the DC side.
        translate([-eps,ac_gland_y,ac_gland_z])
            rotate([0,90,0]) cylinder(h=wall+2*eps,d=ac_gland_d);

        // Bottom intake under the PSU secondary half.
        for (i=[0:7])
            translate([psu_x0+58+i*4.7,psu_y0+11,-eps])
                cube([vent_slot_w,28,floor_t+2*eps]);

        // Opposed narrow lower-wall exhaust slots, above the PCB plane.
        for (i=[0:6]) {
            translate([outer_x-wall-eps,18+i*10,12]) cube([wall+2*eps,2.0,18]);
            translate([-eps,18+i*10,12]) cube([wall+2*eps,2.0,18]);
        }
    }
}

module controller_support(kx,ky) {
    translate([bx(kx)-support_size/2,by(ky)-support_size/2,separator_t-eps])
        cube([support_size,support_size,support_h+eps]);
}

module controller_supports() {
    for (p=[[24,6],[136,6],[6,94],[154,80]]) controller_support(p[0],p[1]);
}

module side_slot(side,ky,width,height=field_cutout_h,zoff=0.3) {
    yy=by(ky)-width/2;
    xx=side=="left" ? -eps : outer_x-wall-eps;
    translate([xx,yy,board_z_local+zoff]) cube([wall+2*eps,width,height]);
}

module front_slot(kx,width) {
    translate([bx(kx)-width/2,-eps,board_z_local+0.3])
        cube([width,wall+2*eps,field_cutout_h]);
}

module snap_pocket(side,yy) {
    pocket_z=upper_h+snap_tab_local_z-0.15;
    xx=side=="left" ? -eps : outer_x-snap_tab_depth-0.15;
    translate([xx,yy-snap_tab_w/2-0.25,pocket_z])
        cube([snap_tab_depth+0.20+eps,snap_tab_w+0.50,snap_tab_h+0.30]);
}

module controller_deck() {
    difference() {
        union() {
            // Solid mains/SELV separator plus upper tray walls.
            rounded_prism(outer_x,outer_y,separator_t,corner_r);
            difference() {
                rounded_prism(outer_x,outer_y,upper_h,corner_r);
                translate([wall,wall,separator_t])
                    rounded_prism(outer_x-2*wall,outer_y-2*wall,upper_h-separator_t+2*eps,
                                  max(0.8,corner_r-wall));
            }
            controller_supports();
        }

        // Tool-required deck attachment; heads fit below the controller PCB.
        for (p=deck_screw_xy)
            translate([p[0],p[1],-eps]) cylinder(h=separator_t+2*eps,d=deck_screw_d);

        // 24 V feedthrough on the PSU secondary side. Fit a certified closed
        // snap bushing/grommet sized for the actual two-core harness; the hole
        // must not remain open in service.
        translate([outer_x-wall-9,outer_y/2,-eps])
            cylinder(h=separator_t+2*eps,d=8.2);

        // Controller wall openings.
        side_slot("left",18.0,13.0);  // J1 24 V
        side_slot("left",48.0,13.0);  // J2 fan
        side_slot("right",70.0,13.0); // J3 SSR
        side_slot("right",52.0,13.0); // J4 thermocouple
        side_slot("right",31.0,usb_cutout_w,usb_cutout_h,0.1); // J5 USB-C
        front_slot(128.0,20.0);        // J6 ESC

        for (yy=snap_centers_y) {
            snap_pocket("left",yy);
            snap_pocket("right",yy);
        }
    }
}

lid_inner_x=outer_x+2*snap_clearance;
lid_inner_y=outer_y+2*snap_clearance;
lid_outer_x=lid_inner_x+2*skirt_t;
lid_outer_y=lid_inner_y+2*skirt_t;
lid_x0=-(snap_clearance+skirt_t);
lid_y0=-(snap_clearance+skirt_t);
lid_corner_r=corner_r+snap_clearance+skirt_t;

module lid_plate() {
    translate([lid_x0,lid_y0,0]) rounded_prism(lid_outer_x,lid_outer_y,lid_t,lid_corner_r);
}
module lid_skirt() {
    translate([0,0,-skirt_h]) difference() {
        translate([lid_x0,lid_y0,0])
            rounded_prism(lid_outer_x,lid_outer_y,skirt_h+eps,lid_corner_r);
        translate([-snap_clearance,-snap_clearance,-eps])
            rounded_prism(lid_inner_x,lid_inner_y,skirt_h+3*eps,corner_r+snap_clearance);
    }
}
module lid_snap_nubs() {
    for (yy=snap_centers_y) {
        translate([-snap_clearance-0.10,yy-snap_tab_w/2,snap_tab_local_z])
            cube([snap_clearance+snap_tab_depth+0.10,snap_tab_w,snap_tab_h]);
        translate([outer_x-snap_tab_depth,yy-snap_tab_w/2,snap_tab_local_z])
            cube([snap_clearance+snap_tab_depth+0.10,snap_tab_w,snap_tab_h]);
    }
}
module lid_hold_down(kx,ky,sx,sy) {
    post_h=clear_above_pcb-hold_down_gap;
    translate([bx(kx)-sx/2,by(ky)-sy/2,-post_h]) cube([sx,sy,post_h+0.20]);
}
module lid_hold_downs() {
    lid_hold_down(20,2,7,3); lid_hold_down(140,2,7,3);
    lid_hold_down(20,98,7,3); lid_hold_down(80,98,7,3);
    lid_hold_down(2,70,3,7); lid_hold_down(158,85,3,7);
}
module lid_cutouts() {
    // RESET and BOOT access.
    for (p=[[50,8],[28,28]])
        translate([bx(p[0]),by(p[1]),-eps]) cylinder(h=lid_t+2*eps,r=2.2);

    // Upper power-stage exhaust, away from the ESP32 antenna region.
    vent_y=by(69.0);
    for (i=[0:7])
        translate([bx(24.0)+i*5.5,vent_y-10,-eps]) cube([2.8,20,lid_t+2*eps]);

    // Snap-arm reliefs and pry notch.
    for (center=snap_centers_y)
        for (yy=[center-snap_tab_w/2,center+snap_tab_w/2]) {
            translate([lid_x0-eps,yy-snap_relief_w/2,-skirt_h-eps])
                cube([skirt_t+2*eps,snap_relief_w,skirt_h-snap_top_bridge+2*eps]);
            translate([outer_x+snap_clearance-eps,yy-snap_relief_w/2,-skirt_h-eps])
                cube([skirt_t+2*eps,snap_relief_w,skirt_h-snap_top_bridge+2*eps]);
        }
    translate([bx(80)-pry_notch_w/2,lid_y0-eps,-skirt_h-eps])
        cube([pry_notch_w,skirt_t+2*eps,pry_notch_h]);
}
module lid() {
    difference() {
        union() { lid_plate(); lid_skirt(); lid_snap_nubs(); lid_hold_downs(); }
        lid_cutouts();
    }
}
module lid_print() { translate([0,outer_y,lid_t]) rotate([180,0,0]) lid(); }

module psu_proxy() {
    color([0.04,0.48,0.16]) translate([psu_x0,psu_y0,psu_z0]) cube([psu_x,psu_y,1.6]);
    color([0.55,0.58,0.62,0.85]) translate([psu_x0+3,psu_y0+3,psu_z0+1.6])
        cube([psu_x-6,psu_y-6,psu_h-1.6]);
    color([0.82,0.72,0.28]) for (ix=[0:1],iy=[0:1])
        translate([psu_hole_x(ix),psu_hole_y(iy),floor_t]) cylinder(h=psu_standoff_h,d=6.0);
}
module pcb_proxy() {
    color([0.03,0.55,0.18]) {
        translate([board_x0,board_y0,board_z_local]) cube([pcb_x,pcb_y,pcb_t]);
        translate([bx(156.325)-3.7,by(31)-4.5,board_top_local]) cube([7.4,9.0,3.3]);
        translate([bx(42.46)-5.25,by(58)-2.4,board_top_local+3]) cube([10.5,4.8,18]);
        translate([bx(7.46),by(23.2),board_top_local]) cylinder(h=16,r=4.2);
        translate([bx(85)-9,by(28)-12.75,board_top_local]) cube([18,25.5,3.2]);
    }
}
module closed_assembly() {
    color([0.40,0.44,0.50]) lower_base();
    psu_proxy();
    color([0.60,0.66,0.72]) translate([0,0,lower_h]) controller_deck();
    translate([0,0,lower_h]) pcb_proxy();
    color([0.12,0.36,0.72]) translate([0,0,lower_h+upper_h]) lid();
}
module exploded_assembly() {
    color([0.40,0.44,0.50]) lower_base();
    psu_proxy();
    color([0.60,0.66,0.72]) translate([outer_x+18,0,lower_h+8]) controller_deck();
    translate([outer_x+18,0,lower_h+8]) pcb_proxy();
    color([0.12,0.36,0.72]) translate([2*(outer_x+18),0,lower_h+upper_h+16]) lid();
}

if (part=="lower_base") lower_base();
else if (part=="controller_deck") controller_deck();
else if (part=="lid") lid();
else if (part=="lid_print") lid_print();
else if (part=="psu_proxy") psu_proxy();
else if (part=="pcb_proxy") pcb_proxy();
else if (part=="exploded") exploded_assembly();
else closed_assembly();
