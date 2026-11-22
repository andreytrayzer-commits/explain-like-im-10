"""Backdrop plate test: can this machine render a lit, foggy 3D scene?

Geometry is deliberately primitive - a floor, blocks for a skyline, cylinders
for rebar - because in the reference the expensive-looking part is the light
and the haze, not the modelling.
"""
import bpy, math, sys, os, time

_arg = sys.argv[sys.argv.index("--") + 1] if "--" in sys.argv else "plate.png"
# Blender resolves a bare relative path against the .blend file, and with no
# .blend open that landed at the drive root, where writing is refused.
OUT = os.path.abspath(_arg)

# --- clean slate
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene

# --- render settings: Eevee, vertical, modest samples
# Eevee needs a GPU context, which cannot be created headless on this machine
# (it crashes in GPU_context_create). Cycles renders on the CPU and works.
sc.render.engine = "CYCLES"

# Use the GPU when the machine has one. OptiX on an RTX card is the whole
# reason for running this elsewhere; fall back to CPU so the same script still
# works on the Mac.
_prefs = bpy.context.preferences.addons.get("cycles")
sc.cycles.device = "CPU"
if _prefs:
    cp = _prefs.preferences
    for backend in ("OPTIX", "CUDA", "HIP", "METAL", "ONEAPI"):
        try:
            cp.compute_device_type = backend
        except TypeError:
            continue
        cp.get_devices()
        gpus = [d for d in cp.devices if d.type != "CPU"]
        if gpus:
            for d in cp.devices:
                d.use = (d.type != "CPU")
            sc.cycles.device = "GPU"
            print(f"@@DEVICE {backend}: " + ", ".join(d.name for d in gpus))
            break
if sc.cycles.device == "CPU":
    print("@@DEVICE CPU")
sc.cycles.samples = int(os.environ.get("SAMPLES", 48))
sc.cycles.use_denoising = True
sc.cycles.max_bounces = 4
sc.cycles.volume_bounces = 1
sc.cycles.volume_step_rate = 4.0
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.resolution_percentage = 100
sc.render.film_transparent = False
sc.render.image_settings.file_format = "PNG"
sc.render.filepath = OUT


# --- world: dark blue, slight ambient
world = bpy.data.worlds.new("w"); sc.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.08, 0.14, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.6


def mat(name, rgb, rough=0.8):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    return m


concrete = mat("concrete", (0.42, 0.45, 0.49))
rust = mat("rust", (0.60, 0.33, 0.14), 0.7)
dark = mat("dark", (0.07, 0.10, 0.16))

# --- floor slab
bpy.ops.mesh.primitive_plane_add(size=90, location=(0, 0, 0))
bpy.context.object.data.materials.append(concrete)

# --- skyline: blocks at distance
import random
random.seed(7)
for i in range(16):
    x = random.uniform(-40, 40); y = random.uniform(26, 48)
    h = random.uniform(8, 26); w = random.uniform(3, 7)
    bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, h / 2))
    o = bpy.context.object; o.scale = (w, w, h); o.data.materials.append(dark)

# --- rebar
for i, (x, y, tilt) in enumerate(((3.2, -1.0, 0.12), (4.0, -0.4, -0.05), (4.8, -1.4, 0.18))):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=4.2, location=(x, y, 2.1))
    o = bpy.context.object; o.rotation_euler = (tilt, tilt * 0.6, 0)
    o.data.materials.append(rust)

# --- the light does the work
bpy.ops.object.light_add(type="SPOT", location=(-2.0, -1.0, 9.0))
sp = bpy.context.object
sp.data.energy = 9000
sp.data.spot_size = math.radians(48)
sp.data.spot_blend = 0.55
sp.data.shadow_soft_size = 0.6
sp.rotation_euler = (0.18, 0, 0)

# --- fog: a volume cube over the whole set
bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 10, 10))
vol = bpy.context.object; vol.scale = (100, 70, 26)
vm = bpy.data.materials.new("fog"); vm.use_nodes = True
nt = vm.node_tree
for n in list(nt.nodes):
    if n.type != "OUTPUT_MATERIAL":
        nt.nodes.remove(n)
pv = nt.nodes.new("ShaderNodeVolumePrincipled")
pv.inputs["Density"].default_value = 0.012
pv.inputs["Color"].default_value = (0.55, 0.66, 0.80, 1)
nt.links.new(pv.outputs["Volume"], nt.nodes["Material Output"].inputs["Volume"])
vol.data.materials.append(vm)

# --- camera: low, looking slightly up, portrait
bpy.ops.object.camera_add(location=(0, -14, 2.2))
cam = bpy.context.object
cam.rotation_euler = (math.radians(84), 0, 0)
cam.data.lens = 34
sc.camera = cam

t0 = time.time()
bpy.ops.render.render(write_still=True)
print(f"@@RENDER_SECONDS {time.time() - t0:.1f}")
print(f"@@SAVED {OUT}")
