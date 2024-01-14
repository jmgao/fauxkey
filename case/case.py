import cadquery as cq

# Case wall thickness
case_base_thickness = 1.60
case_front_thickness = case_base_thickness
case_back_thickness = case_base_thickness
case_side_thickness = case_base_thickness + 2.0
case_top_thickness = case_base_thickness
case_bottom_thickness = case_base_thickness

case_fillet_radius = 1.6
case_inset_thickness = 0.8
case_inset_depth = 1.2

# 2.4mm actual, but leave .2mm of extra space for the hole
nut_height = 2.6
nut_diameter = 6.3
nut_depth = 0.6

screw_inset = 3.75
screw_thread_diameter = 3.0
screw_head_diameter = 5.8
screw_head_depth = 2.0

pcb_width = 58.500
pcb_height = 26.300

# Standoffs below the key PCB
bottom_standoff_thickness = 3

key_thickness = 1.0

# Shim between the key and fauxkey
shim_thickness = 3.40

# 0.8mm PCB
fauxkey_thickness = 0.80

# ~6.0mm from reverse mounting the Mill-Max 0850
fauxkey_component_thickness = 3.6

# Cutout in the side of the case for the cable
usb_cutout_width = 8.5
usb_cutout_height = 2.8

def fauxkey_total_thickness():
    return fauxkey_thickness + fauxkey_component_thickness

def total_thickness():
    return case_top_thickness + fauxkey_total_thickness() + shim_thickness + key_thickness + bottom_standoff_thickness + case_bottom_thickness

def midpoint():
    return total_thickness() / 2

def above_cutout():
    return usb_cutout_height / 2 + fauxkey_total_thickness() + case_top_thickness

def below_cutout():
    return shim_thickness + key_thickness + bottom_standoff_thickness + case_bottom_thickness - usb_cutout_height / 2

log(f"above = {above_cutout()}")
log(f"below = {below_cutout()}")
if above_cutout() > below_cutout():
    case_bottom_thickness += above_cutout() - below_cutout()
else:
    case_top_thickness += below_cutout() - above_cutout()
    
log(f"midpoint = {midpoint()}")
log(f"total = {total_thickness()}")

usb_cutout_offset = usb_cutout_height / 2 + fauxkey_total_thickness() + case_top_thickness

# Cutout in the shim for the USB-C connector
usb_connector_width = 10
usb_connector_height = 9

key_outline = cq.importers.importDXF("./pcb.dxf")
shim_outline = cq.importers.importDXF("./shim.dxf")
fauxkey_outline = cq.importers.importDXF("./fauxkey.dxf")

def generate_extrusion(outline, thickness):
    return outline.wires().toPending().extrude(thickness).translate((case_front_thickness, case_side_thickness))
                    
def generate_case():
    case = (
        cq.Workplane("XY")
            .box(
                case_front_thickness  + pcb_width + case_back_thickness,
                pcb_height + case_side_thickness * 2,
                case_bottom_thickness
                    + bottom_standoff_thickness
                    + key_thickness
                    + shim_thickness
                    + fauxkey_total_thickness()
                    + case_top_thickness,
                    centered=(False, False, False))
            .edges("|Z")
            .fillet(case_fillet_radius)
    )

    # Key standoffs
    standoff_x_coordinates = (4.5, 16.5, 54)
    standoff_y_coordinates = (pcb_height / 2, pcb_height / 2, pcb_height / 2)
    standoff_widths = (9, 4, 9)
    standoff_heights = (pcb_height, 10, pcb_height)
    

    cutout_thickness = bottom_standoff_thickness + key_thickness + shim_thickness + fauxkey_thickness + fauxkey_component_thickness
    cutout_offset = case_top_thickness + fauxkey_total_thickness() - fauxkey_thickness - fauxkey_component_thickness
    cutout = generate_extrusion(key_outline, cutout_thickness).translate((0, 0, cutout_offset))

    for (x, y, width, height) in zip(standoff_x_coordinates, standoff_y_coordinates, standoff_widths, standoff_heights):
        cutout = (
            cutout
                .faces(">Z")
                .workplane(centerOption="CenterOfBoundBox", invert=True)
                .move(-pcb_width/2 + x)
                .box(width, height, bottom_standoff_thickness, centered=(True, True, False), combine="cut")
        )
        
    # Fauxkey standoff
    cutout = (
        cutout
            .faces("<Z")
            .workplane(centerOption="CenterOfBoundBox", invert=True)
            .move(-pcb_width / 2, 0)
            .box(usb_connector_width, usb_connector_height, fauxkey_component_thickness, centered=(True, True, False), combine="cut")
    )
    return case - cutout

def generate_shim():
    # TODO: Move holes from DXF to code, so the dimensions can be configured
    shim = generate_extrusion(shim_outline, shim_thickness)

    # Dimensions relative to PCB orientation
    usb_c_thickness = shim_thickness
    shim = (
        shim
            .faces(">Z")
            .workplane(centerOption="CenterOfBoundBox", invert=True)
            .move(-pcb_width/2, 0)
            .box(usb_connector_height, usb_connector_width, shim_thickness, centered=(False, True, False), combine="cut")
    )

    return shim

fauxkey = (
    generate_extrusion(fauxkey_outline, fauxkey_thickness)
        .translate((0, 0, fauxkey_total_thickness() - fauxkey_thickness + case_top_thickness))
)
shim = (
    generate_shim()
        .translate((0, 0, fauxkey_total_thickness() + case_top_thickness))
)
key = (
    generate_extrusion(key_outline, key_thickness)
        .translate((0, 0, shim_thickness + fauxkey_total_thickness() + case_top_thickness))
)

log("wtf")
case = generate_case()

total_width = pcb_width + case_front_thickness + case_back_thickness
total_height = pcb_height + case_side_thickness * 2
total_depth = midpoint() * 2

use_nut = False

if use_nut:
    case = (
        case
            .faces("<Z")
            .workplane(offset=nut_depth, centerOption="CenterOfBoundBox", invert=True)
            .rect(total_width - screw_inset * 2, total_height - screw_inset * 2, forConstruction=True)
            .vertices()
            .polygon(6, nut_diameter, forConstruction=True)
            .toPending()
            .extrude(nut_height, combine="cut")
    )


case = (
    case
    .faces(">Z")
    .workplane(centerOption="CenterOfBoundBox")
    .rect(total_width - screw_inset * 2, total_height - screw_inset * 2, forConstruction=True)
    .vertices()
    .cskHole(screw_thread_diameter, screw_head_diameter, 82, total_depth - nut_depth)
)

split_offset = -midpoint() - case_inset_depth
split_plane = case.faces(">Z").workplane(offset=split_offset)

index = (
    cq.Sketch()
        .rect(total_width, total_height)
        .vertices()
        .fillet(case_fillet_radius)
        .reset()
        .rect(total_width - case_inset_thickness * 2, total_height - case_inset_thickness * 2, mode='s')
        .vertices()
        .fillet(0.8)
        
)

top = split_plane.split(keepTop=True)
bottom = split_plane.split(keepBottom=True)

top = (
   top
       .faces("<Z")
       .workplane(centerOption="CenterOfBoundBox", invert=True)
       .placeSketch(index)
       .cutBlind(case_inset_depth)
)

bottom = (
   bottom
       .faces(">Z")
       .workplane(centerOption="CenterOfBoundBox")
       .placeSketch(index)
       .extrude(case_inset_depth)
)

usb_cutout_sketch = (
    cq.Sketch()
        .rect(usb_cutout_width, usb_cutout_height)
        .vertices()
        .fillet(1)
)

log(f"origin = {(0, pcb_height / 2 + case_side_thickness, midpoint())}")
top = (
    top
        .faces("<X")
        .workplane(invert=True, centerOption="ProjectedOrigin", origin=(0, pcb_height / 2 + case_side_thickness, midpoint()))
        .placeSketch(usb_cutout_sketch)
        .cutBlind(case_front_thickness)
)

bottom = (
    bottom
        .faces("<X")
        .workplane(invert=True, centerOption="ProjectedOrigin", origin=(0, pcb_height / 2 + case_side_thickness, midpoint()))
        .placeSketch(usb_cutout_sketch)
        .cutBlind(case_front_thickness)
)

#show_object(key, name="Key", options=dict(alpha=0.25, color='brown'))
#show_object(shim, name="Shim", options=dict(alpha=0.25,color='red'))
show_object(fauxkey, name="fauxkey", options=dict(alpha=0.25, color='green'))
show_object(top, name="Top", options=dict(alpha=0, color='red'))
show_object(bottom, name="Bottom", options=dict(alpha=0, color='yellow'))