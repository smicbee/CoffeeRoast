#!/usr/bin/env python3
"""Add future MIC/LCD/button connectors to the RevD schematic.

Requires kiutils 1.4.8. The operation is idempotent and deliberately adds only
hardware connectivity; firmware ownership is deferred.
"""
from copy import deepcopy
from pathlib import Path
from uuid import uuid4

from kiutils.schematic import Schematic

ROOT = Path(__file__).resolve().parents[1]
SCH = ROOT / "CoffeeRoast-Control-RevD-Balanced.kicad_sch"
PROJECT = "CoffeeRoast-Control-RevD-Balanced"
FOOTPRINT = "Connector_PinHeader_1.27mm:PinHeader_1x06_P1.27mm_Vertical"

CONNECTORS = (
    ("J7", "MIC_I2S_FUTURE", (80.01, 245.11),
     ("+3V3", "GND", "GPIO4", "GPIO5", "GPIO6", "GPIO7")),
    ("J8", "LCD_I2C_FUTURE", (200.66, 245.11),
     ("+3V3", "GND", "GPIO8", "GPIO9", "GPIO14", "GPIO21")),
    ("J9", "BUTTONS_4_FUTURE", (320.04, 245.11),
     ("GND", "GPIO15", "GPIO16", "GPIO17", "GPIO18", "+3V3")),
)


def prop(symbol, key):
    return next(p for p in symbol.properties if p.key == key)


def shift_position(position, dx, dy):
    position.X += dx
    position.Y += dy


sch = Schematic.from_file(str(SCH))
existing = {prop(s, "Reference").value for s in sch.schematicSymbols}
if all(ref in existing for ref, *_ in CONNECTORS):
    print("RevD UI connectors already present; no schematic changes made")
    raise SystemExit(0)
if any(ref in existing for ref, *_ in CONNECTORS):
    raise SystemExit("Partial UI connector set found; refusing ambiguous update")

base = next(s for s in sch.schematicSymbols if prop(s, "Reference").value == "JGPIO1")
label_template = next(g for g in sch.globalLabels if g.text == "GPIO3")
wire_template = next(
    w for w in sch.graphicalItems
    if getattr(w, "type", None) == "wire"
    and len(w.points) == 2
    and abs(abs(w.points[1].X - w.points[0].X) - 1.27) < 1e-6
)

for ref, value, (x, y), nets in CONNECTORS:
    symbol = deepcopy(base)
    dx = x - symbol.position.X
    dy = y - symbol.position.Y
    shift_position(symbol.position, dx, dy)
    symbol.uuid = str(uuid4())
    symbol.pins = {str(i): str(uuid4()) for i in range(1, 7)}
    for p in symbol.properties:
        shift_position(p.position, dx, dy)
    prop(symbol, "Reference").value = ref
    prop(symbol, "Value").value = value
    prop(symbol, "Footprint").value = FOOTPRINT
    prop(symbol, "Reference").position.X = x + 3.81
    prop(symbol, "Reference").position.Y = y - 7.62
    prop(symbol, "Value").position.X = x + 6.35
    prop(symbol, "Value").position.Y = y + 10.16
    for hidden_key in ("Footprint", "Datasheet", "Description"):
        hidden_property = prop(symbol, hidden_key)
        if hidden_property.effects is not None:
            hidden_property.effects.hide = True
    for instance in symbol.instances:
        instance.name = PROJECT
        for path in instance.paths:
            path.reference = ref
    sch.schematicSymbols.append(symbol)

    # Conn_01x06 pins are at x-5.08 and y+[-5.08,-2.54,0,2.54,5.08,7.62].
    for index, net in enumerate(nets):
        pin_y = y - 5.08 + index * 2.54
        pin_x = x - 5.08
        label_x = pin_x - 1.27

        wire = deepcopy(wire_template)
        wire.uuid = str(uuid4())
        wire.points[0].X, wire.points[0].Y = label_x, pin_y
        wire.points[1].X, wire.points[1].Y = pin_x, pin_y
        sch.graphicalItems.append(wire)

        label = deepcopy(label_template)
        label.uuid = str(uuid4())
        label.text = net
        label.position.X, label.position.Y, label.position.angle = label_x, pin_y, 180
        for p in label.properties:
            p.position.X, p.position.Y = label_x, pin_y
        sch.globalLabels.append(label)

if sch.titleBlock is not None:
    sch.titleBlock.revision = "D-UI"
    sch.titleBlock.comments[2] = (
        "Future I2S microphone, I2C LCD and four-button connectors; firmware deferred"
    )
sch.to_file(str(SCH))
print("Added J7 MIC, J8 LCD and J9 four-button connectors to RevD schematic")
