from ursina import *
from ursina.prefabs.draggable import Draggable

# ———————————————————————————————————————
# App Setup
# ———————————————————————————————————————
app = Ursina()
window.vsync = False

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
        if held_keys['left mouse']:
            if mouse.hovered_entity == self.knob:
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
        super().__init__(parent=camera.ui, model='circle', collider='box',
                         position=position, color=color, scale=.1, z=-0.1, **kwargs)
        self.key_name = key_name

    # def on_press(self):
    #     held_keys[self.key_name] = 1
    #     invoke(lambda: input(self.key_name), delay=0)

    # def on_release(self):
    #     held_keys[self.key_name] = 0
    #     input(f'{self.key_name} up')

    def on_click(self):
        held_keys[self.key_name] = 1
        input(self.key_name)

    def input(self, key):
        if key == f'{self.key_name} up':
            held_keys[self.key_name] = 0

# ———————————————————————————————————————
# First Person Controller
# ———————————————————————————————————————

class FirstPersonController(Entity):
    def __init__(self, **kwargs):
        super().__init__()
        self.cursor = Entity(parent=camera.ui, model='quad', color=color.pink, scale=.008, rotation_z=45)
        self.speed = 5
        self.height = 2
        self.camera_pivot = Entity(parent=self, y=self.height)
        camera.parent = self.camera_pivot
        camera.position = (0, 0, 0)
        camera.rotation = (0, 0, 0)
        camera.fov = 90

        self.use_touch = True
        mouse.locked = False
        mouse.visible = True
        self.mouse_sensitivity = Vec2(40, 40)

        self.gravity = 1
        self.grounded = False
        self.jump_height = 2
        self.jump_up_duration = .5
        self.fall_after = .35
        self.air_time = 0

        self.traverse_target = scene
        self.ignore_list = [self]
        self.gun = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.gravity:
            ray = raycast(self.world_position + (0, self.height, 0), self.down,
                          traverse_target=self.traverse_target, ignore=self.ignore_list)
            if ray.hit:
                self.y = ray.world_point.y

    def update(self):
        if self.use_touch:
            rot = joystick_look.value
            self.rotation_y += rot.x * time.dt * 100
            self.camera_pivot.rotation_x = clamp(
                self.camera_pivot.rotation_x + rot.y * time.dt * 50, -90, 90)

        move = joystick_move.value
        direction = Vec3(self.forward * move.y + self.right * move.x).normalized()

        if direction:
            feet = raycast(self.position + Vec3(0, .5, 0), direction,
                           traverse_target=self.traverse_target, ignore=self.ignore_list, distance=.5)
            head = raycast(self.position + Vec3(0, self.height - .1, 0), direction,
                           traverse_target=self.traverse_target, ignore=self.ignore_list, distance=.5)
            if not (feet.hit or head.hit):
                self.position += direction * self.speed * time.dt

        if self.gravity:
            down_ray = raycast(self.world_position + (0, self.height, 0), self.down,
                               traverse_target=self.traverse_target, ignore=self.ignore_list)
            if down_ray.distance <= self.height + .1 and down_ray.world_normal.y > .7:
                if not self.grounded:
                    self.land()
                self.grounded = True
                self.y = down_ray.world_point.y
            else:
                self.grounded = False
                self.y -= min(self.air_time, down_ray.distance - .05) * time.dt * 100
                self.air_time += time.dt * .25 * self.gravity

    def input(self, key):
        if key == 't':
            self.use_touch = not self.use_touch
            mouse.locked = not self.use_touch

        if key in ('space', 'gamepad a'):
            self.jump()

        # Only shoot if not clicking a UI element
        if key == 'left mouse down' and self.gun and not mouse.hovered_entity in (joystick_move.knob, joystick_look.knob, button_jump, button_shoot):
            self.shoot()

        if key == 'gamepad x':
            self.shoot()

    def jump(self):
        if not self.grounded:
            return
        self.grounded = False
        self.animate_y(self.y + self.jump_height, self.jump_up_duration,
                       resolution=int(1 // time.dt), curve=curve.out_expo)
        invoke(self.start_fall, delay=self.fall_after)

    def start_fall(self):
        # No y_animator by default, use manual animation state handling
        self.air_time += time.dt

    def land(self):
        self.air_time = 0
        self.grounded = True

    def shoot(self):
        if not self.gun:
            return
        self.gun.blink(color.orange)
        bullet = Entity(parent=self.gun, model='cube', scale=.1, color=color.black)
        bullet.world_parent = scene
        bullet.animate_position(bullet.position + (bullet.forward * 50),
                                curve=curve.linear, duration=1)
        destroy(bullet, delay=1)

# ———————————————————————————————————————
# Scene Setup
# ———————————————————————————————————————

joystick_move = VirtualJoystick(position=(-.7, -.3))
joystick_look = VirtualJoystick(position=(.3, -.3))
button_jump = VirtualButton('gamepad a',  position=(.6, -.1), color=color.lime)
button_shoot = VirtualButton('gamepad x', position=(.8, -.2), color=color.red)

ground = Entity(model='plane', scale=(100, 1, 100), color=color.yellow.tint(-.2),
                texture='white_cube', texture_scale=(100, 100), collider='box')
wall1 = Entity(model='cube', scale=(1, 5, 10), x=2, y=.01, rotation_y=45,
               collider='box', texture='white_cube')
wall1.texture_scale = (wall1.scale_z, wall1.scale_y)
wall2 = Entity(model='cube', scale=(1, 5, 10), x=-2, y=.01,
               collider='box', texture='white_cube')
wall2.texture_scale = (wall2.scale_z, wall2.scale_y)

player = FirstPersonController(y=2, origin_y=-.5)
gun = Button(parent=scene, model='cube', color=color.blue,
             origin_y=-.5, position=(3, 0, 3), collider='box', scale=(.2, .2, 1))
gun.on_click = lambda: (setattr(gun, 'parent', camera), setattr(gun, 'position', Vec3(.5, 0, .5)), setattr(player, 'gun', gun))

hook = Button(parent=scene, model='cube', color=color.brown, position=(4, 5, 5))
hook.on_click = Func(player.animate_position, hook.position, duration=.5, curve=curve.linear)

button_jump.on_click = player.jump
button_shoot.on_click = player.shoot

Sky()

# ———————————————————————————————————————
# Global Update
# ———————————————————————————————————————

def update():
    if mouse.left and mouse.hovered_entity and isinstance(mouse.hovered_entity, Button):
        return

# ———————————————————————————————————————
# Run App
# ———————————————————————————————————————
app.run()
