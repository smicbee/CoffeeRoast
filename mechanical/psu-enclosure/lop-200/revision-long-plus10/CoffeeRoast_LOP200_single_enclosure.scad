/*
 * CoffeeRoast — single Mean Well LOP-200-24 protective enclosure
 *
 * Exact PSU contract: 101.6 x 50.8 x 25.4 mm, 95.25 x 44.45 mm
 * mounting pattern, 4x3.3 mm holes, M3 conductive pillars per Mean Well.
 *
 * SAFETY PROTOTYPE ONLY. A printed shell is not certification. Final assembly
 * requires UL94-V-0 material, certified cable glands, conductive M3 pillars,
 * protective-earth bonding, fuse/switch/strain-relief review, touch-probe
 * assessment and thermal testing by a qualified person.
 */

$fn = 64;
part = is_undef(part) ? "closed" : part;

// Mean Well LOP-200 mechanical contract.
psu_x = 101.6;
psu_y = 50.8;
psu_h = 25.4;
psu_hole_dx = 95.25;
psu_hole_dy = 44.45;
psu_hole_d = 3.3;
psu_hole_offset = 3.175;

// Printed shell.
wall = 2.4;
floor_t = 2.4;
lid_t = 2.4;
end_clear = 13.0; // 5 mm extra cable space at each end along X
side_clear = 8.0; // includes Mean Well's ±1 mm mechanical tolerance
standoff_h = 6.0;       // physical conductive M3 pillars, not printed posts
clear_above = 6.0;
corner_r = 4.0;

inner_x = psu_x + 2*end_clear;
inner_y = psu_y + 2*side_clear;
outer_x = inner_x + 2*wall;
outer_y = inner_y + 2*wall;
base_h = floor_t + standoff_h + psu_h + clear_above;
closed_h = base_h + lid_t;
psu_x0 = wall + end_clear;
psu_y0 = wall + side_clear;
psu_z0 = floor_t + standoff_h;

// M16/PG11-class cable glands; verify against actual cable outside diameter.
gland_hole_d = 16.2;
gland_z = 20.0;
ac_gland_y = psu_y0 + 34.0;
dc_gland_y = psu_y0 + 27.0;

// Lid M3 screws into heat-set inserts in four inaccessible internal bosses.
lid_boss_d = 7.2;
lid_boss_center = 5.8;
lid_insert_d = 4.2;
lid_insert_depth = 6.0;
lid_screw_d = 3.4;

vent_slot_w = 2.0;
vent_slot_l = 30.0;
vent_pitch = 6.0;
vent_count = 12;

eps = 0.05;

function psu_hole_x(ix) = psu_x0 + psu_hole_offset + ix*psu_hole_dx;
function psu_hole_y(iy) = psu_y0 + psu_hole_offset + iy*psu_hole_dy;
function boss_x(ix) = ix == 0 ? lid_boss_center : outer_x-lid_boss_center;
function boss_y(iy) = iy == 0 ? lid_boss_center : outer_y-lid_boss_center;

module rounded_prism(x,y,z,r) {
    linear_extrude(height=z)
        offset(r=r)
            translate([r,r]) square([x-2*r,y-2*r]);
}

module lid_bosses() {
    for (ix=[0:1], iy=[0:1])
        translate([boss_x(ix),boss_y(iy),floor_t-eps])
            cylinder(h=base_h-floor_t+eps,d=lid_boss_d);
}

module base_shell() {
    difference() {
        union() {
            difference() {
                rounded_prism(outer_x,outer_y,base_h,corner_r);
                translate([wall,wall,floor_t])
                    rounded_prism(inner_x,inner_y,base_h-floor_t+2*eps,
                                  max(0.8,corner_r-wall));
            }
            lid_bosses();
        }

        // Exact four PSU mounting holes; use conductive M3 pillars above floor.
        for (ix=[0:1],iy=[0:1]) {
            translate([psu_hole_x(ix),psu_hole_y(iy),-eps])
                cylinder(h=floor_t+2*eps,d=3.4);
            // Shallow external recess for low-profile M3 screw heads.
            translate([psu_hole_x(ix),psu_hole_y(iy),-eps])
                cylinder(h=1.0+eps,d=6.4);
        }

        // Heat-set insert bores open from the base top.
        for (ix=[0:1],iy=[0:1])
            translate([boss_x(ix),boss_y(iy),base_h-lid_insert_depth])
                cylinder(h=lid_insert_depth+eps,d=lid_insert_d);

        // Opposed AC and SELV cable-gland holes.
        translate([-eps,ac_gland_y,gland_z])
            rotate([0,90,0]) cylinder(h=wall+2*eps,d=gland_hole_d);
        translate([outer_x-wall-eps,dc_gland_y,gland_z])
            rotate([0,90,0]) cylinder(h=wall+2*eps,d=gland_hole_d);

        // Bottom inlet slots only under the low-voltage half of the PCB.
        for (i=[0:7])
            translate([psu_x0+58+i*4.7,psu_y0+10,-eps])
                cube([vent_slot_w,30,floor_t+2*eps]);
    }
}

module lid_raw() {
    rounded_prism(outer_x,outer_y,lid_t,corner_r);
}

module lid() {
    difference() {
        lid_raw();

        // Four captive-access screws: lid cannot be opened without a tool.
        for (ix=[0:1],iy=[0:1])
            translate([boss_x(ix),boss_y(iy),-eps])
                cylinder(h=lid_t+2*eps,d=lid_screw_d);

        // Narrow top exhaust slots: 2 mm width limits direct finger access.
        start_x = (outer_x-(vent_count-1)*vent_pitch-vent_slot_w)/2;
        for (i=[0:vent_count-1])
            translate([start_x+i*vent_pitch,(outer_y-vent_slot_l)/2,-eps])
                cube([vent_slot_w,vent_slot_l,lid_t+2*eps]);

        // Permanent recessed hazard and side labels.
        translate([outer_x/2,outer_y-8,lid_t-0.6])
            linear_extrude(height=0.7)
                text("230V AC - PE REQUIRED",size=4.0,halign="center",valign="center",
                     font="Liberation Sans:style=Bold");
        translate([11,8,lid_t-0.6])
            linear_extrude(height=0.7)
                text("AC",size=4.0,halign="center",valign="center",
                     font="Liberation Sans:style=Bold");
        translate([outer_x-13,8,lid_t-0.6])
            linear_extrude(height=0.7)
                text("24V",size=4.0,halign="center",valign="center",
                     font="Liberation Sans:style=Bold");
    }
}

module psu_proxy() {
    color([0.04,0.48,0.16])
        translate([psu_x0,psu_y0,psu_z0]) cube([psu_x,psu_y,1.6]);
    color([0.55,0.58,0.62,0.85])
        translate([psu_x0+3,psu_y0+3,psu_z0+1.6])
            cube([psu_x-6,psu_y-6,psu_h-1.6]);
    color([0.82,0.72,0.28])
        for (ix=[0:1],iy=[0:1])
            translate([psu_hole_x(ix),psu_hole_y(iy),floor_t])
                cylinder(h=standoff_h,d=6.0);
}

module closed_assembly() {
    color([0.52,0.58,0.65]) base_shell();
    psu_proxy();
    color([0.15,0.34,0.70]) translate([0,0,base_h]) lid();
}

module open_assembly() {
    color([0.52,0.58,0.65]) base_shell();
    psu_proxy();
    color([0.15,0.34,0.70]) translate([outer_x+14,0,base_h+8]) lid();
}

if (part=="base") base_shell();
else if (part=="lid") lid();
else if (part=="psu_proxy") psu_proxy();
else if (part=="open") open_assembly();
else closed_assembly();
