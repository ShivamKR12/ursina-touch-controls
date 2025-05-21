from ursina import *
from ursina.prefabs.draggable import Draggable

# ———————————————————————————————————————
# On-Screen Controls
# ———————————————————————————————————————
class VirtualJoystick(Entity):
    """An on-screen joystick for touch input (2 axes → Vec2)."""
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
    """An on-screen button with a simple is_pressed state."""
    def __init__(self, text, position=(0,0), **kwargs):
        super().__init__(
            parent=camera.ui, model='circle', collider='box',
            text=text, scale=.1, position=position, **kwargs
        )
        self.is_pressed = False

    def on_press(self):
        self.is_pressed = True
        return True

    def on_release(self):
        self.is_pressed = False
        return True

# ———————————————————————————————————————
# Main App
# ———————————————————————————————————————
if __name__ == '__main__':
    app = Ursina()
    window.title = '6-DOF Camera Demo'
    window.borderless = False

    # 1) Static cube at world origin
    Entity(model='cube', color=color.azure, scale=1)

    # 2) Camera pivot to allow full rotation & translation
    pivot = Entity()
    camera.parent   = pivot
    camera.position = Vec3(0,0,-5)
    camera.look_at(Vec3(0,0,0))

    # 3) On-screen controls
    joy_move   = VirtualJoystick(position=(-.7, -.3))  # left stick for TX/TY
    joy_look   = VirtualJoystick(position=( .3, -.3))  # right stick for yaw/pitch

    # Z translation buttons
    btn_forward  = VirtualButton(text='w', position=(.7, .0), color=color.lime)
    btn_backward = VirtualButton(text='s', position=(.8, .0), color=color.red)

    # Roll buttons
    btn_roll_ccw = VirtualButton(text='q', position=(.7,-.1), color=color.cyan)
    btn_roll_cw  = VirtualButton(text='e', position=(.8,-.1), color=color.yellow)

    move_speed = 4
    rot_speed  = 100

    def update():
        # refresh joysticks
        joy_move.update()
        joy_look.update()

        dt = time.dt

        # --- Translation
        tx = joy_move.value.x           # X-axis
        ty = joy_move.value.y           # Y-axis
        tz = int(btn_forward.is_pressed) - int(btn_backward.is_pressed)

        pivot.position += Vec3(tx, ty, tz) * dt * move_speed

        # --- Rotation
        yaw   = joy_look.value.x        # yaw about world-up
        pitch = joy_look.value.y        # pitch about local-right
        roll  = int(btn_roll_cw.is_pressed) - int(btn_roll_ccw.is_pressed)

        pivot.rotation_y += yaw   * dt * rot_speed
        pivot.rotation_x += pitch * dt * rot_speed
        pivot.rotation_z += roll  * dt * rot_speed

    app.run()
