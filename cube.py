from ursina import *
from ursina.prefabs.draggable import Draggable
import random
import time

# ———————————————————————————————————————
# On-Screen Controls (for 6-DOF camera)
# ———————————————————————————————————————
class VirtualJoystick(Entity):
    def __init__(self, radius=80, position=(0,0), **kwargs):
        super().__init__(parent=camera.ui, position=position, scale=(.2,.2), **kwargs)
        self.radius = radius / 100
        self.bg     = Entity(parent=self, model='circle', color=color.dark_gray, scale=2)
        self.knob   = Draggable(parent=self, model='circle', color=color.white, scale=1)
        self.knob.always_on_top  = True
        self.knob.start_position = self.knob.position
        self.value = Vec2(0,0)

    def update(self):
        if self.knob.dragging:
            off = Vec2(self.knob.position.x, self.knob.position.y)
            if off.length() > self.radius:
                off = off.normalized() * self.radius
            self.knob.position = Vec3(off.x, off.y, self.knob.position.z)
            self.value = off / self.radius
        else:
            self.knob.position = self.knob.start_position
            self.value = Vec2(0,0)

class VirtualButton(Button):
    def __init__(self, text, position=(0,0), **kwargs):
        super().__init__(
            parent=camera.ui, model='circle', collider='box',
            text=text, scale=.15, position=position, **kwargs
        )
        self.is_pressed = False
    def on_press(self):
        self.is_pressed = True
        return True
    def on_release(self):
        self.is_pressed = False
        return True

# ———————————————————————————————————————
# Rubik’s-Cube logic (intact from your original)
# ———————————————————————————————————————
app = Ursina()
window.title      = 'Rubik’s Cube + 6-DOF Camera'
window.borderless = False
window.color      = color._16

# build one 6-face mesh
cube_colors = [
    color.pink, color.orange,
    color.white, color.yellow,
    color.azure, color.green,
]
combine_parent = Entity(enabled=False)
for i, direction in enumerate((Vec3.right, Vec3.up, Vec3.forward)):
    f = Entity(parent=combine_parent, model='plane', origin_y=-.5,
               texture='white_cube', color=cube_colors[i*2])
    f.look_at(direction, Vec3.up)
    f2 = Entity(parent=combine_parent, model='plane', origin_y=-.5,
               texture='white_cube', color=cube_colors[i*2+1])
    f2.look_at(-direction, Vec3.up)
combine_parent.combine()

# place 3×3×3 cubes around origin
cubes = []
for x in range(3):
    for y in range(3):
        for z in range(3):
            e = Entity(
                model=copy(combine_parent.model),
                position=Vec3(x,y,z) - (Vec3(3,3,3)/3),
                texture='white_cube'
            )
            cubes.append(e)

# face-click collider
collider = Entity(model='cube', scale=3, collider='box', visible=False)

def collider_input(key):
    # ignore clicks if interacting with UI
    if hasattr(mouse.hovered_entity, 'world_parent') and mouse.hovered_entity.world_parent == camera.ui:
        return
    if mouse.hovered_entity == collider:
        if key == 'left mouse down':
            rotate_side(mouse.normal, 1)
        elif key == 'right mouse down':
            rotate_side(mouse.normal, -1)
collider.input = collider_input

rotation_helper = Entity()
win_text_entity = Text(y=.35, text='', color=color.green, origin=(0,0), scale=3)

def rotate_side(normal, direction=1, speed=1):
    # attach correct cubes to pivot
    if normal == Vec3(1,0,0):
        [setattr(e, 'world_parent', rotation_helper) for e in cubes if e.x > 0]
        rotation_helper.animate('rotation_x',  90*direction, duration=.15*speed, curve=curve.linear)
    elif normal == Vec3(-1,0,0):
        [setattr(e, 'world_parent', rotation_helper) for e in cubes if e.x < 0]
        rotation_helper.animate('rotation_x', -90*direction, duration=.15*speed, curve=curve.linear)
    elif normal == Vec3(0,1,0):
        [setattr(e, 'world_parent', rotation_helper) for e in cubes if e.y > 0]
        rotation_helper.animate('rotation_y',  90*direction, duration=.15*speed, curve=curve.linear)
    elif normal == Vec3(0,-1,0):
        [setattr(e, 'world_parent', rotation_helper) for e in cubes if e.y < 0]
        rotation_helper.animate('rotation_y', -90*direction, duration=.15*speed, curve=curve.linear)
    elif normal == Vec3(0,0,1):
        [setattr(e, 'world_parent', rotation_helper) for e in cubes if e.z > 0]
        rotation_helper.animate('rotation_z', -90*direction, duration=.15*speed, curve=curve.linear)
    elif normal == Vec3(0,0,-1):
        [setattr(e, 'world_parent', rotation_helper) for e in cubes if e.z < 0]
        rotation_helper.animate('rotation_z',  90*direction, duration=.15*speed, curve=curve.linear)

    invoke(reset_rotation_helper, delay=.2*speed)
    if speed:
        collider.ignore_input = True
        @after(.25*speed)
        def _():
            collider.ignore_input = False
            check_for_win()

def reset_rotation_helper():
    [setattr(e, 'world_parent', scene) for e in cubes]
    rotation_helper.rotation = (0,0,0)

def check_for_win():
    if {e.world_rotation for e in cubes} == {Vec3(0,0,0)}:
        win_text_entity.text = 'SOLVED!'
        win_text_entity.appear()
    else:
        win_text_entity.text = ''

def randomize():
    faces = (Vec3(1,0,0),Vec3(0,1,0),Vec3(0,0,1),
             Vec3(-1,0,0),Vec3(0,-1,0),Vec3(0,0,-1))
    for i in range(20):
        rotate_side(random.choice(faces), random.choice((-1,1)), speed=0)

Button(text='randomize', color=color.azure, position=(.7,-.4), on_click=randomize).fit_to_text()

# ———————————————————————————————————————
# 6-DOF Camera Setup
# ———————————————————————————————————————
pivot = Entity()
camera.parent   = pivot
camera.position = Vec3(0,0,-10)
camera.look_at(Vec3(0,0,0))

joy_move   = VirtualJoystick(position=(-.7, -.3))
joy_look   = VirtualJoystick(position=( .3, -.3))
btn_fwd    = VirtualButton('FORWARD',    position=(.6, .1),   color=color.lime)
btn_back   = VirtualButton('BACK',       position=(.8, .1),    color=color.red)
btn_roll_l = VirtualButton('ROLL-LEFT',  position=(.6,-.1),   color=color.cyan)
btn_roll_r = VirtualButton('ROLL-RIGHT', position=(.8,-.1), color=color.yellow)

move_speed = 4
rot_speed  = 100

def update():
    # -- Rubik’s-cube face UI should not block camera-UI clicks
    joy_move.update()
    joy_look.update()

    # camera translation
    tx = joy_move.value.x
    ty = joy_move.value.y
    tz = int(btn_fwd.is_pressed) - int(btn_back.is_pressed)
    pivot.position += Vec3(tx, ty, tz) * time.dt * move_speed

    # camera rotation
    yaw   = joy_look.value.x
    pitch = joy_look.value.y
    roll  = int(btn_roll_r.is_pressed) - int(btn_roll_l.is_pressed)
    pivot.rotation_y += yaw   * time.dt * rot_speed
    pivot.rotation_x += pitch * time.dt * rot_speed
    pivot.rotation_z += roll  * time.dt * rot_speed

    # keep collider at cube origin
    collider.position = Vec3(0,0,0)

# ———————————————————————————————————————
# Issues to watch for
# ———————————————————————————————————————
# 1) UI vs cube input: we filter out clicks when the hovered_entity is under camera.ui,
#    but Draggable knobs can sometimes still absorb clicks—ensure your UI areas don’t overlap the cube screen projection.
# 2) Performance: using 27 separate Entities (no instancing) plus animation can be heavier;
#    if you scale up, consider swapping to instanced Entities with a shared instance_id.
# 3) Font glyphs: if you replace 'W/S/Q/E' with arrows, make sure your font supports those unicode chars.

app.run()
