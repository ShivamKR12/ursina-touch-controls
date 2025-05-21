from ursina import *
from ursina.prefabs.draggable import Draggable
from ursina.prefabs.first_person_controller import FirstPersonController
from ursina.shaders import lit_with_shadows_shader
import random

# ———————————————————————————————————————
# App Setup
# ———————————————————————————————————————
app = Ursina()
window.vsync = False
random.seed(0)
Entity.default_shader = lit_with_shadows_shader

# ———————————————————————————————————————
# Utility: check if pointer is over UI
# ———————————————————————————————————————
def is_clicking_ui():
    return mouse.hovered_entity and mouse.hovered_entity.has_ancestor(camera.ui)

# ———————————————————————————————————————
# UI: Virtual Joystick and Button
# ———————————————————————————————————————
class VirtualJoystick(Entity):
    def __init__(self, radius=80, position=(-.7, -.4), **kwargs):
        super().__init__(parent=camera.ui, position=position, scale=(.2, .2), **kwargs)
        self.bg = Entity(parent=self, model='circle', color=color.dark_gray, scale=2)
        self.knob = Draggable(parent=self, model='circle', color=color.white, scale=1, z=-1)
        self.radius = radius / 100
        self.knob.start_position = self.knob.position
        self.value = Vec2(0, 0)

    def update(self):
        # begin drag on first touch
        if held_keys['left mouse'] and mouse.hovered_entity == self.knob:
            self.knob.dragging = True

        if self.knob.dragging:
            offset = Vec2(self.knob.position.x, self.knob.position.y)
            if offset.length() > self.radius:
                offset = offset.normalized() * self.radius
            self.knob.position = offset
            self.value = offset / self.radius
        else:
            self.knob.position = self.knob.start_position
            self.value = Vec2(0, 0)

class VirtualButton(Button):
    def __init__(self, key_name='space', position=(.7, -.4), color=color.azure, **kwargs):
        super().__init__(
            parent=camera.ui, model='circle', collider='box',
            position=position, color=color, scale=.1, z=-0.1, **kwargs
        )
        self.key_name = key_name

    def on_click(self):
        held_keys[self.key_name] = 1
        invoke(lambda: input(self.key_name), delay=0)

    def input(self, key):
        if key == f'{self.key_name} up':
            held_keys[self.key_name] = 0

# ———————————————————————————————————————
# Scene: ground and shootable blocks
# ———————————————————————————————————————
ground = Entity(model='plane', collider='box', scale=64,
                texture='grass', texture_scale=(4,4))

shootables_parent = Entity()
mouse.traverse_target = shootables_parent

for i in range(16):
    Entity(
        parent=shootables_parent,
        model='cube', origin_y=-.5, scale=2,
        texture='brick', texture_scale=(1,2),
        x=random.uniform(-8,8),
        z=random.uniform(-8,8)+8,
        collider='box',
        scale_y=random.uniform(2,3),
        color=color.hsv(0,0, random.uniform(.9,1))
    )

# ———————————————————————————————————————
# First‐person player & gun
# ———————————————————————————————————————
player = FirstPersonController(
    model='cube', z=-10, color=color.orange,
    origin_y=-.5, speed=8, collider='box'
)
player.collider = BoxCollider(player, Vec3(0,1,0), Vec3(1,2,1))
player.use_touch       = True
player.camera_pivot    = Entity(parent=player, y=player.height)
camera.parent          = player.camera_pivot
camera.position        = (0,0,0)
camera.rotation        = (0,0,0)
player.mouse_sensitivity = Vec2(40,40)
# (and ensure player.traverse_target, player.ignore_list exist)
player.traverse_target = scene
player.ignore_list     = [player]
mouse.locked = False
mouse.visible = True
player.mouse_sensitivity = Vec2(0, 0)

gun = Entity(
    model='cube', parent=camera,
    position=(.5,-.25,.25), scale=(.3,.2,1),
    origin_z=-.5, color=color.red
)
gun.on_cooldown = False
gun.muzzle_flash = Entity(
    parent=gun, z=1, world_scale=.5,
    model='quad', color=color.yellow, enabled=False
)
player.gun = gun  # allow FPC to know about the gun

# ———————————————————————————————————————
# Shooting logic (with bullet + muzzle flash)
# ———————————————————————————————————————
def shoot():
    if gun.on_cooldown: 
        return
    
    gun.parent = camera
    gun.position = Vec3(.5, -0.25, .25)
    gun.rotation = Vec3(0, 0, 0)

    gun.on_cooldown = True

    # muzzle flash + sound
    gun.muzzle_flash.enabled = True
    from ursina.prefabs.ursfx import ursfx
    ursfx(
        [(0.0,0.0),(0.1,0.9),(0.15,0.75),(0.3,0.14),(0.6,0.0)],
        volume=0.5, wave='noise',
        pitch=random.uniform(-13,-12), pitch_change=-12, speed=3.0
    )
    invoke(gun.muzzle_flash.disable, delay=.05)
    invoke(setattr, gun, 'on_cooldown', False, delay=.15)

    # spawn bullet
    bullet = Entity(parent=gun, 
                    model='cube', 
                    scale=.1, color=color.black)
    bullet.world_parent = scene
    bullet.animate_position(bullet.position + gun.forward * 50, curve=curve.linear, duration=1)
    destroy(bullet, delay=1)

    # damage hit target
    if mouse.hovered_entity and hasattr(mouse.hovered_entity, 'hp'):
        mouse.hovered_entity.hp -= 10
        mouse.hovered_entity.blink(color.red)

# ———————————————————————————————————————
# Input handling
# ———————————————————————————————————————
def update():
    # touch‐based movement & look
    if player.use_touch:
        rot = joystick_look.value
        player.rotation_y += rot.x * time.dt * 100
        player.camera_pivot.rotation_x = clamp(
            player.camera_pivot.rotation_x + rot.y * time.dt * 50, -90, 90
        )

        move = joystick_move.value
        direction = Vec3(player.forward * move.y + player.right * move.x).normalized()
        if direction:
            feet = raycast(player.position + Vec3(0,.5,0), direction,
                           traverse_target=player.traverse_target,
                           ignore=player.ignore_list, distance=.5)
            head = raycast(player.position + Vec3(0,player.height-.1,0), direction,
                           traverse_target=player.traverse_target,
                           ignore=player.ignore_list, distance=.5)
            if not (feet.hit or head.hit):
                player.position += direction * player.speed * time.dt

    # continuous fire on desktop when not over UI
    if held_keys['left mouse'] and not is_clicking_ui():
        shoot()

def input(key):
    # toggle touch mode
    if key == 't':
        player.use_touch = not player.use_touch
        mouse.locked = not player.use_touch

    # jump
    if key in ('space', 'gamepad a'):
        player.jump()

    # shoot on click/tap (blocked over UI)
    if key == 'left mouse down' and not is_clicking_ui():
        shoot()
    if key == 'gamepad x':
        shoot()

# ———————————————————————————————————————
# Instantiate UI controls
# ———————————————————————————————————————
joystick_move = VirtualJoystick(position=(-.7, -.3))
joystick_look = VirtualJoystick(position=( .3, -.3))
button_jump = VirtualButton('gamepad a',  position=(.6, -.1), color=color.lime)
button_shoot = VirtualButton('gamepad x', position=(.8, -.2), color=color.red)

# link virtual buttons to actions
button_jump.on_click = lambda: input('space')
button_shoot.on_click = lambda: input('gamepad x')

# ———————————————————————————————————————
# Enemy class & spawn
# ———————————————————————————————————————
class Enemy(Entity):
    def __init__(self, **kwargs):
        super().__init__(parent=shootables_parent,
                         model='cube', scale_y=2, origin_y=-.5,
                         color=color.light_gray, collider='box', **kwargs)
        self.health_bar = Entity(
            parent=self, y=1.2, model='cube',
            color=color.red, world_scale=(1.5,.1,.1)
        )
        self.max_hp = 100
        self._hp = self.max_hp

    def update(self):
        dist = distance_xz(player.position, self.position)
        if dist > 40:
            return
        self.health_bar.alpha = max(0, self.health_bar.alpha - time.dt)
        self.look_at_2d(player.position, 'y')
        hit = raycast(self.world_position + Vec3(0,1,0),
                      self.forward, 30, ignore=(self,))
        if hit.entity == player and dist > 2:
            self.position += self.forward * time.dt * 5

    @property
    def hp(self):
        return self._hp

    @hp.setter
    def hp(self, value):
        self._hp = value
        if value <= 0:
            destroy(self)
            return
        self.health_bar.world_scale_x = (value/self.max_hp)*1.5
        self.health_bar.alpha = 1

enemies = [Enemy(x=x*4) for x in range(4)]

# ———————————————————————————————————————
# Final setup: sky & lighting
# ———————————————————————————————————————
sun = DirectionalLight()
sun.look_at(Vec3(1,-1,-1))
Sky()

app.run()
