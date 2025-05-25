from ursina import *
from ursina.prefabs.draggable import Draggable

# ———————————————————————————————————————
# App Setup
# ———————————————————————————————————————
app = Ursina()
window.vsync = False  # disable vsync for uncapped framerate

# ———————————————————————————————————————
# UI: Virtual Joystick and Button
# ———————————————————————————————————————

class VirtualJoystick(Entity):
    """
    An on-screen joystick control that:
      1. Scales its base and knob dynamically based on window size.
      2. Allows dragging within its circular radius.
      3. Reports a Vec2 value in the range [-1, +1].
    """
    def __init__(
        self,
        radius: float = 50,
        knob_factor: float = 2.5,
        position: tuple = (-.7, -.4),
        **kwargs
    ):
        super().__init__(parent=camera.ui, position=position, **kwargs)
        self.knob_factor = knob_factor

        # 1) Store pixel dimensions for base and knob
        self.diameter_px = radius * 2
        self.radius_px   = radius

        # 2) Capture initial window size for ratio calculations
        self._init_w, self._init_h = window.size

        # 3) Compute “base” UI-space scales (height-only)
        h = self._init_h or 1
        self._base_ui_diam   = (self.diameter_px / h) * 2
        self._base_ui_radius = (self.radius_px   / h) * 2

        # 4) Build visual elements
        self.bg = Entity(
            parent=self,
            model='circle',
            color=color.rgba32(64, 64, 64, 150)
        )
        self.knob = Draggable(
            parent=self,
            model='circle',
            color=color.white
        )
        self.knob.always_on_top   = True
        self.knob.start_position  = Vec2(0, 0)

        # 6) Current input value (Vec2)
        self.value = Vec2(0, 0)

        # 7) Initialize with no width-ratio scaling (ratio=1.0)
        self._apply_scale(1.0)

    def _apply_scale(self, ratio: float) -> None:
        """
        Apply dynamic scaling to:
          - self.scale    (joystick base diameter)
          - bg.scale      (fills its parent)
          - knob.scale    (knob diameter * knob_factor)
          - max_offset    (limit for dragging)
        """
        ui_d = self._base_ui_diam * ratio
        ui_r = self._base_ui_radius * ratio

        self.scale      = Vec2(ui_d, ui_d)
        self.bg.scale   = Vec2(1, 1)  # base circle fills parent Entity
        self.knob.scale = Vec2(ui_r * self.knob_factor,
                               ui_r * self.knob_factor)
        
        # update max_offset and logical radius here, once ui_r is known
        self.max_offset = (ui_r * self.knob_factor) / 2
        self.radius     = self.max_offset

    def update(self) -> None:
        # Recompute width-ratio if window width changed
        cur_w, _ = window.size
        ratio    = cur_w / (self._init_w or cur_w)
        self._apply_scale(ratio)

        # Begin dragging if mouse is held over the knob
        if held_keys['left mouse'] and mouse.hovered_entity == self.knob:
            self.knob.dragging = True

        # While dragging, clamp knob to circle and compute value
        if self.knob.dragging:
            offset = Vec2(self.knob.position.x, self.knob.position.y)
            if offset.length() > self.radius:
                offset = offset.normalized() * self.radius
            self.knob.position = offset
            self.value = offset / self.radius
        else:
            # Reset knob when released
            self.knob.position = self.knob.start_position
            self.value = Vec2(0, 0)


class VirtualButton(Button):
    """
    An on-screen button that:
      1. Scales dynamically with window width.
      2. Sets held_keys[key_name] on click and release.
    """
    def __init__(
        self,
        key_name: str = 'space',
        size_px: float = 40,
        position: tuple = (.7, -.4),
        color: Color = color.azure,
        **kwargs
    ):
        super().__init__(
            parent=camera.ui,
            model='circle',
            collider='box',
            position=position,
            color=color,
            **kwargs
        )
        self.key_name = key_name
        self.size_px  = size_px

        # 1) Store initial window dimensions
        self._init_w, self._init_h = window.size

        # 2) Compute base UI scale from height
        h = self._init_h or 1
        self._base_ui_size = (self.size_px / h) * 2

        # 3) Apply initial scale with no width-ratio change
        self.scale = self._base_ui_size

    def update(self) -> None:
        # Recompute width ratio and apply to scale
        cur_w, _ = window.size
        ratio    = cur_w / (self._init_w or cur_w)
        self.scale = self._base_ui_size * ratio

    def on_click(self) -> None:
        """Called when the user clicks the button."""
        held_keys[self.key_name] = 1
        input(self.key_name)

    def input(self, key: str) -> None:
        """Called on input events—used here to reset held_keys."""
        if key == f'{self.key_name} up':
            held_keys[self.key_name] = 0


# ———————————————————————————————————————
# First Person Controller
# ———————————————————————————————————————

class FirstPersonController(Entity):
    """
    A basic first-person character:
      - Mouse/touch look using virtual joysticks.
      - WASD or joystick movement with collision.
      - Jump, gravity, and optional gun shooting.
    """
    def __init__(self, **kwargs):
        super().__init__()

        # 1) On-screen cursor
        self.cursor = Entity(
            parent=camera.ui,
            model='quad',
            color=color.pink,
            scale=.008,
            rotation_z=45
        )

        # 2) Movement parameters
        self.speed            = 5
        self.height           = 2
        self.camera_pivot     = Entity(parent=self, y=self.height)
        camera.parent        = self.camera_pivot
        camera.position      = (0, 0, 0)
        camera.rotation      = (0, 0, 0)
        camera.fov           = 90
        self.use_touch       = True
        mouse.locked         = False
        mouse.visible        = True
        self.mouse_sensitivity = Vec2(40, 40)

        # 3) Jump & gravity
        self.gravity          = 1
        self.grounded         = False
        self.jump_height      = 2
        self.jump_up_duration = .5
        self.fall_after       = .35
        self.air_time         = 0

        # 4) Collision setup
        self.traverse_target = scene
        self.ignore_list     = [self]
        self.gun             = None

        # Apply any overrides passed in
        for key, value in kwargs.items():
            setattr(self, key, value)

        # Snap to ground on spawn
        if self.gravity:
            ray = raycast(
                self.world_position + (0, self.height, 0),
                self.down,
                traverse_target=self.traverse_target,
                ignore=self.ignore_list
            )
            if ray.hit:
                self.y = ray.world_point.y

    def update(self) -> None:
        # 1) Look via right joystick
        if self.use_touch:
            rot = joystick_look.value
            yaw_gain   = 100
            pitch_gain = 100
            self.rotation_y += rot.x * time.dt * yaw_gain
            self.camera_pivot.rotation_x = clamp(
                self.camera_pivot.rotation_x + rot.y * time.dt * pitch_gain,
                -90,
                90
            )

        # 2) Move via left joystick
        move      = joystick_move.value
        direction = Vec3(self.forward * move.y + self.right * move.x).normalized()

        if direction:
            # Prevent walking through walls
            feet = raycast(
                self.position + Vec3(0, .5, 0),
                direction,
                traverse_target=self.traverse_target,
                ignore=self.ignore_list,
                distance=.5
            )
            head = raycast(
                self.position + Vec3(0, self.height - .1, 0),
                direction,
                traverse_target=self.traverse_target,
                ignore=self.ignore_list,
                distance=.5
            )
            if not (feet.hit or head.hit):
                self.position += direction * self.speed * time.dt

        # 3) Gravity & landing
        if self.gravity:
            down_ray = raycast(
                self.world_position + (0, self.height, 0),
                self.down,
                traverse_target=self.traverse_target,
                ignore=self.ignore_list
            )
            if down_ray.distance <= self.height + .1 and down_ray.world_normal.y > .7:
                if not self.grounded:
                    self.land()
                self.grounded = True
                self.y = down_ray.world_point.y
            else:
                self.grounded = False
                self.y -= min(
                    self.air_time,
                    down_ray.distance - .05
                ) * time.dt * 100
                self.air_time += time.dt * .25 * self.gravity

    def input(self, key: str) -> None:
        # Toggle touch controls
        if key == 't':
            self.use_touch  = not self.use_touch
            mouse.locked    = not self.use_touch

        # Jump
        if key in ('space', 'gamepad a'):
            self.jump()

        # Shoot (if gun equipped and not clicking UI)
        if key == 'left mouse down' and self.gun \
           and mouse.hovered_entity not in (
               joystick_move.knob,
               joystick_look.knob,
               button_jump,
               button_shoot
           ):
            self.shoot()

        if key == 'gamepad x':
            self.shoot()

    def jump(self) -> None:
        """Animate a jump if grounded."""
        if not self.grounded:
            return
        self.grounded = False
        self.animate_y(
            self.y + self.jump_height,
            self.jump_up_duration,
            resolution=int(1 // time.dt),
            curve=curve.out_expo
        )
        invoke(self.start_fall, delay=self.fall_after)

    def start_fall(self) -> None:
        """Begin manual gravity animation after jump peak."""
        self.air_time += time.dt

    def land(self) -> None:
        """Reset air_time on landing."""
        self.air_time = 0
        self.grounded = True

    def shoot(self) -> None:
        """Fire a bullet from the equipped gun."""
        if not self.gun:
            return
        self.gun.blink(color.orange)
        bullet = Entity(
            parent=self.gun,
            model='cube',
            scale=.1,
            color=color.black
        )
        bullet.world_parent = scene
        bullet.animate_position(
            bullet.position + (bullet.forward * 50),
            curve=curve.linear,
            duration=1
        )
        destroy(bullet, delay=1)


# ———————————————————————————————————————
# Scene Setup
# ———————————————————————————————————————

# Instantiate touch controls
joystick_move  = VirtualJoystick(position=(-.7, -.3))
joystick_look  = VirtualJoystick(position=( .3, -.3))
button_jump    = VirtualButton('gamepad a', position=( .6, -.1), color=color.lime)
button_shoot   = VirtualButton('gamepad x', position=( .8, -.2), color=color.red)

# Add some environment to test collision
ground = Entity(
    model='plane',
    scale=(100, 1, 100),
    color=color.yellow.tint(-.2),
    texture='white_cube',
    texture_scale=(100, 100),
    collider='box'
)
wall1 = Entity(
    model='cube',
    scale=(1, 5, 10),
    x=2,
    y=.01,
    rotation_y=45,
    collider='box',
    texture='white_cube'
)
wall1.texture_scale = (wall1.scale_z, wall1.scale_y)

wall2 = Entity(
    model='cube',
    scale=(1, 5, 10),
    x=-2,
    y=.01,
    collider='box',
    texture='white_cube'
)
wall2.texture_scale = (wall2.scale_z, wall2.scale_y)

# Spawn player and interactive objects
player = FirstPersonController(y=2, origin_y=-.5)
gun = Button(
    parent=scene,
    model='cube',
    color=color.blue,
    origin_y=-.5,
    position=(3, 0, 3),
    collider='box',
    scale=(.2, .2, 1)
)
gun.on_click = lambda: (
    setattr(gun, 'parent', camera),
    setattr(gun, 'position', Vec3(.5, 0, .5)),
    setattr(player, 'gun', gun)
)

hook = Button(
    parent=scene,
    model='cube',
    color=color.brown,
    position=(4, 5, 5)
)
hook.on_click = Func(player.animate_position, hook.position, duration=.5, curve=curve.linear)

# Bind button callbacks to player actions
button_jump.on_click  = player.jump
button_shoot.on_click = player.shoot

Sky()  # add a skybox

# ———————————————————————————————————————
# Global Update (prevent clicks through UI)
# ———————————————————————————————————————
def update():
    if mouse.left and isinstance(mouse.hovered_entity, Button):
        return

# ———————————————————————————————————————
# Run App
# ———————————————————————————————————————
app.run()
