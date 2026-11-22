#!/usr/bin/env python3
"""Render the backdrop plate library.

Plates are rendered once and reused across every episode, which is why a few
minutes each is acceptable. Geometry stays primitive - the look comes from one
light and a fog volume, as in the reference.

    blender -b -P blender/plates.py -- out_dir [only_name]
"""
import bpy, math, os, sys, time

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUTDIR = os.path.abspath(ARGS[0] if ARGS else "plates")
ONLY = ARGS[1] if len(ARGS) > 1 else None
SAMPLES = int(os.environ.get("SAMPLES", 24))
W, H = 1080, 1920


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    sc.render.resolution_x, sc.render.resolution_y = W, H
    sc.render.image_settings.file_format = "PNG"
    sc.cycles.samples = SAMPLES
    sc.cycles.use_denoising = True
    sc.cycles.max_bounces = 3
    sc.cycles.volume_bounces = 1
    sc.cycles.volume_step_rate = 5.0
    sc.cycles.device = "CPU"
    p = bpy.context.preferences.addons.get("cycles")
    if p:
        cp = p.preferences
        for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
            try:
                cp.compute_device_type = backend
            except TypeError:
                continue
            cp.get_devices()
            if [d for d in cp.devices if d.type != "CPU"]:
                for d in cp.devices:
                    d.use = d.type != "CPU"
                sc.cycles.device = "GPU"
                break
    return sc


def mat(name, rgb, rough=.85, emit=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*rgb, 1)
        b.inputs["Emission Strength"].default_value = emit
    return m


def box(x, y, z, sx, sy, sz, m):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z))
    o = bpy.context.object; o.scale = (sx, sy, sz)
    o.data.materials.append(m); return o


def fog(density=.011, colour=(.55, .66, .80)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 8, 9))
    v = bpy.context.object; v.scale = (90, 70, 24)
    vm = bpy.data.materials.new("fog"); vm.use_nodes = True
    nt = vm.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    pv = nt.nodes.new("ShaderNodeVolumePrincipled")
    pv.inputs["Density"].default_value = density
    pv.inputs["Color"].default_value = (*colour, 1)
    nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
    v.data.materials.append(vm)


def camera(sc, loc=(0, -13, 2.4), pitch=85, lens=32):
    bpy.ops.object.camera_add(location=loc)
    c = bpy.context.object
    c.rotation_euler = (math.radians(pitch), 0, 0)
    c.data.lens = lens
    sc.camera = c


def world(sc, rgb=(.05, .08, .14), strength=.6):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (*rgb, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = strength


# ---------------------------------------------------------------- the plates

def p_mansion(sc):
    world(sc, (.06, .07, .10), .5)
    floor = mat("marble", (.46, .44, .42), .25)
    wall = mat("wall", (.30, .28, .27))
    glass = mat("glow", (1.0, .78, .42), .4, emit=9)
    gold = mat("gold", (.78, .60, .22), .25)
    bpy.ops.mesh.primitive_plane_add(size=80); bpy.context.object.data.materials.append(floor)
    box(0, 14, 7, 34, .6, 14, wall)
    for x in (-8.5, 8.5):
        box(x, 13.6, 6, 5.2, .3, 8, glass)
    box(0, 13.4, 5.2, 3.2, .3, 7, gold)
    bpy.ops.object.light_add(type="AREA", location=(0, 2, 9))
    L = bpy.context.object; L.data.energy = 2200; L.data.size = 7
    L.data.color = (1.0, .84, .62); L.rotation_euler = (math.radians(12), 0, 0)
    fog(.010, (.70, .62, .50)); camera(sc, (0, -13, 2.6), 86, 30)


def p_empty(sc):
    world(sc, (.05, .06, .09), .35)
    floor = mat("concrete", (.38, .39, .41))
    wall = mat("wall", (.26, .27, .29))
    bulb = mat("bulb", (1.0, .86, .58), .3, emit=28)
    crate = mat("crate", (.36, .28, .18))
    bpy.ops.mesh.primitive_plane_add(size=80); bpy.context.object.data.materials.append(floor)
    box(0, 14, 7, 34, .6, 14, wall)
    box(-7, 4, .9, 2.0, 1.6, 1.8, crate)
    box(-5.6, 5.4, .6, 1.4, 1.2, 1.2, crate)
    box(7.4, 5, .8, 1.8, 1.5, 1.6, crate)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=.28, location=(0, 3, 6.2))
    bpy.context.object.data.materials.append(bulb)
    bpy.ops.object.light_add(type="POINT", location=(0, 3, 6.1))
    L = bpy.context.object; L.data.energy = 900; L.data.color = (1.0, .85, .6)
    L.data.shadow_soft_size = .5
    fog(.014, (.62, .66, .74)); camera(sc, (0, -12, 2.4), 86, 32)


def p_office(sc):
    world(sc, (.06, .07, .10), .45)
    floor = mat("floor", (.34, .35, .38))
    wall = mat("wall", (.28, .30, .33))
    metal = mat("metal", (.40, .42, .45), .4)
    paper = mat("paper", (.86, .84, .78))
    lamp = mat("lampglow", (1.0, .88, .66), .3, emit=16)
    bpy.ops.mesh.primitive_plane_add(size=80); bpy.context.object.data.materials.append(floor)
    box(0, 14, 7, 34, .6, 14, wall)
    for x in (-9.5, -7.2, 7.2, 9.5):
        box(x, 12.0, 2.2, 1.9, 1.4, 4.4, metal)
    box(0, 4.5, 1.1, 6.4, 2.6, .25, paper)
    for x in (-2.6, 2.6):
        box(x, 4.5, .55, .3, 2.2, 1.1, metal)
    bpy.ops.mesh.primitive_cylinder_add(radius=.5, depth=.2, location=(2.2, 4.0, 1.5))
    bpy.context.object.data.materials.append(lamp)
    bpy.ops.object.light_add(type="SPOT", location=(2.2, 3.4, 5.4))
    L = bpy.context.object; L.data.energy = 2600; L.data.spot_size = math.radians(70)
    L.data.spot_blend = .6; L.data.color = (1.0, .88, .68); L.rotation_euler = (0.1, 0, 0)
    fog(.009, (.60, .64, .72)); camera(sc, (0, -11, 2.6), 85, 33)


def p_vault(sc):
    world(sc, (.04, .05, .08), .3)
    floor = mat("floor", (.30, .31, .34), .35)
    wall = mat("steel", (.33, .35, .39), .35)
    door = mat("vaultdoor", (.46, .48, .52), .22)
    bpy.ops.mesh.primitive_plane_add(size=80); bpy.context.object.data.materials.append(floor)
    box(0, 12, 7, 34, .6, 14, wall)
    bpy.ops.mesh.primitive_cylinder_add(radius=3.4, depth=.9, location=(0, 11.4, 3.6))
    d = bpy.context.object; d.rotation_euler = (math.radians(90), 0, 0)
    d.data.materials.append(door)
    bpy.ops.mesh.primitive_torus_add(major_radius=1.1, minor_radius=.18, location=(0, 10.9, 3.6))
    t = bpy.context.object; t.rotation_euler = (math.radians(90), 0, 0)
    t.data.materials.append(door)
    bpy.ops.object.light_add(type="SPOT", location=(0, 1, 8.5))
    L = bpy.context.object; L.data.energy = 5200; L.data.spot_size = math.radians(52)
    L.data.spot_blend = .55; L.rotation_euler = (0.30, 0, 0); L.data.shadow_soft_size = .7
    fog(.016, (.58, .64, .76)); camera(sc, (0, -12, 2.8), 85, 34)


def p_street(sc):
    world(sc, (.05, .07, .12), .5)
    road = mat("road", (.26, .28, .31))
    dark = mat("dark", (.08, .10, .15))
    glow = mat("shopglow", (1.0, .76, .40), .35, emit=12)
    bpy.ops.mesh.primitive_plane_add(size=90); bpy.context.object.data.materials.append(road)
    import random
    random.seed(4)
    for i in range(14):
        x = random.uniform(-34, 34); y = random.uniform(20, 44)
        h = random.uniform(7, 24); w = random.uniform(3, 6)
        box(x, y, h / 2, w, w, h, dark)
    box(6.5, 10.5, 2.6, 5.0, .4, 5.2, glow)
    box(6.5, 11.2, 3.2, 6.2, .8, 7.0, dark)
    bpy.ops.object.light_add(type="AREA", location=(6.5, 9.6, 3.0))
    L = bpy.context.object; L.data.energy = 1600; L.data.size = 5
    L.data.color = (1.0, .78, .46); L.rotation_euler = (math.radians(90), 0, 0)
    fog(.013, (.56, .64, .78)); camera(sc, (-1, -13, 2.4), 86, 31)


def p_auction(sc):
    world(sc, (.05, .06, .09), .4)
    floor = mat("floor", (.33, .32, .31), .3)
    wood = mat("wood", (.40, .27, .15))
    seat = mat("seat", (.24, .26, .30))
    bpy.ops.mesh.primitive_plane_add(size=80); bpy.context.object.data.materials.append(floor)
    box(0, 14, 7, 34, .6, 14, mat("wall", (.27, .26, .26)))
    box(0, 8.5, 1.3, 4.2, 1.6, 2.6, wood)
    for r in range(3):
        for c in (-6, -3.2, 3.2, 6):
            box(c, -1.5 + r * 2.4, .7, 1.7, 1.0, 1.4, seat)
    bpy.ops.object.light_add(type="SPOT", location=(0, 5.5, 8.6))
    L = bpy.context.object; L.data.energy = 4200; L.data.spot_size = math.radians(46)
    L.data.spot_blend = .5; L.rotation_euler = (0.22, 0, 0); L.data.shadow_soft_size = .6
    fog(.012, (.64, .62, .66)); camera(sc, (0, -12, 2.8), 85, 32)


PLATES = dict(mansion=p_mansion, empty=p_empty, office=p_office,
              vault=p_vault, street=p_street, auction=p_auction)

os.makedirs(OUTDIR, exist_ok=True)
for name, fn in PLATES.items():
    if ONLY and name != ONLY:
        continue
    sc = reset()
    fn(sc)
    sc.render.filepath = os.path.join(OUTDIR, f"{name}.png")
    t0 = time.time()
    bpy.ops.render.render(write_still=True)
    print(f"@@PLATE {name} {time.time() - t0:.0f}s -> {sc.render.filepath}")
