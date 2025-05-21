from typing import Callable, Optional, List, Dict
from ursina import *
from ursina.prefabs.draggable import Draggable

def mm_to_ui(mm: float, mm_per_px_x: float = 68.0 / 1080) -> float:
    px = mm / mm_per_px_x
    return px / 1080

class VirtualJoystick(Entity):
    def __init__(self, 
                 radius: int = 80, 
                 position: tuple = (-.7, -.4), 
                 sensitivity: float = 1.0, 
                 dead_zone: float = 0.05, 
                 **kwargs
            ):
        super().__init__(parent=camera.ui, 
                         position=position, 
                         scale=(.2, .2), 
                         **kwargs
                    )
        self.radius = radius
        self.sensitivity = sensitivity
        self.dead_zone = dead_zone
        self.bg = Entity(parent=self, model='circle', color=color.dark_gray, scale=2)
        self.knob = Draggable(parent=self, model='circle', color=color.white, scale=1)
        self.knob.always_on_top = True
        self.knob.start_position = self.knob.position
        self.value = Vec2(0, 0)

    def update(self) -> None:
        if self.knob.dragging:
            offset = Vec2(self.knob.position.x, self.knob.position.y)
            max_offset = self.radius / 100
            if offset.length() > max_offset:
                offset = offset.normalized() * max_offset
            self.knob.position = offset
            val = offset * (100 / self.radius) * self.sensitivity
            if val.length() < self.dead_zone:
                val = Vec2(0, 0)
            self.value = val
        else:
            self.knob.position = self.knob.start_position
            self.value = Vec2(0, 0)

class VirtualButton(Button):
    def __init__(self, 
                 key_name: str = 'gamepad a', 
                 position: tuple = (.5, -.4), 
                 color=color.azure, 
                 **kwargs
            ):
        super().__init__(parent=camera.ui, position=position, color=color, scale=.1, **kwargs)
        self.key_name = key_name
        self.is_pressed = False
        self.on_press_callbacks: List[Callable[[str], None]] = []
        self.on_release_callbacks: List[Callable[[str], None]] = []

    def on_press(self) -> None:
        self.is_pressed = True
        held_keys[self.key_name] = 1
        for callback in self.on_press_callbacks:
            callback(self.key_name)

    def on_release(self) -> None:
        self.is_pressed = False
        held_keys[self.key_name] = 0
        for callback in self.on_release_callbacks:
            callback(self.key_name)

    def input(self, key: str) -> None:
        if not self.hovered:
            return
        if key == 'left mouse down':
            self.is_pressed = True
            held_keys[self.key_name] = 1
            for callback in self.on_press_callbacks:
                callback(self.key_name)
        elif key == 'left mouse up':
            self.is_pressed = False
            held_keys[self.key_name] = 0
            for callback in self.on_release_callbacks:
                callback(self.key_name)

    def add_on_press_callback(self, callback: Callable[[str], None]) -> None:
        self.on_press_callbacks.append(callback)

    def add_on_release_callback(self, callback: Callable[[str], None]) -> None:
        self.on_release_callbacks.append(callback)

class InputManager:
    def __init__(self, 
                 entities: Optional[List[Entity]] = None, 
                 enable_onscreen_controls: bool = True, 
                 sensitivity: float = 1.0, 
                 dead_zone: float = 0.05
            ):
        self.entities = entities if entities else []
        self.enable_onscreen_controls = enable_onscreen_controls
        self.sensitivity = sensitivity
        self.dead_zone = dead_zone

        if self.enable_onscreen_controls:
            self.joystick_left = VirtualJoystick(position=(-.7, -.3), 
                                                 sensitivity=self.sensitivity, 
                                                 dead_zone=self.dead_zone)
            self.joystick_right = VirtualJoystick(position=(.3, -.3), 
                                                  sensitivity=self.sensitivity, 
                                                  dead_zone=self.dead_zone)
            self.buttons = [
                VirtualButton('gamepad a', position=(.7, -.1), color=color.lime),
                VirtualButton('gamepad b', position=(.8, -.2), color=color.red),
                VirtualButton('gamepad x', position=(.6, -.2), color=color.cyan),
                VirtualButton('gamepad y', position=(.7, -.3), color=color.yellow)
            ]
        else:
            self.joystick_left = None
            self.joystick_right = None
            self.buttons = []

        self.button_press_callbacks: Dict[str, List[Callable[[str], None]]] = {}
        self.button_release_callbacks: Dict[str, List[Callable[[str], None]]] = {}

        for button in self.buttons:
            button.add_on_press_callback(self._on_button_press)
            button.add_on_release_callback(self._on_button_release)

    def _on_button_press(self, key_name: str) -> None:
        if key_name in self.button_press_callbacks:
            for callback in self.button_press_callbacks[key_name]:
                callback(key_name)

    def _on_button_release(self, key_name: str) -> None:
        if key_name in self.button_release_callbacks:
            for callback in self.button_release_callbacks[key_name]:
                callback(key_name)

    def register_button_press_callback(self, key_name: str, callback: Callable[[str], None]) -> None:
        if key_name not in self.button_press_callbacks:
            self.button_press_callbacks[key_name] = []
        self.button_press_callbacks[key_name].append(callback)

    def register_button_release_callback(self, key_name: str, callback: Callable[[str], None]) -> None:
        if key_name not in self.button_release_callbacks:
            self.button_release_callbacks[key_name] = []
        self.button_release_callbacks[key_name].append(callback)

    def update(self) -> None:
        if self.enable_onscreen_controls:
            self.joystick_left.update()
            self.joystick_right.update()

        dt = time.dt
        for entity in self.entities:
            if self.enable_onscreen_controls and self.joystick_left and self.joystick_right:
                move_x = self.joystick_left.value.x * dt * 4 * self.sensitivity
                move_z = self.joystick_left.value.y * dt * 4 * self.sensitivity
                entity.position += entity.right * move_x + entity.forward * move_z

                rot_y = self.joystick_right.value.x * dt * 100 * self.sensitivity
                rot_x = -self.joystick_right.value.y * dt * 50 * self.sensitivity
                entity.rotation_y += rot_y
                entity.rotation_x += rot_x

    def get_axis(self, axis_name: str) -> float:
        if not self.enable_onscreen_controls:
            return 0.0
        if axis_name == 'left_x':
            return self.joystick_left.value.x if self.joystick_left else 0.0
        elif axis_name == 'left_y':
            return self.joystick_left.value.y if self.joystick_left else 0.0
        elif axis_name == 'right_x':
            return self.joystick_right.value.x if self.joystick_right else 0.0
        elif axis_name == 'right_y':
            return self.joystick_right.value.y if self.joystick_right else 0.0
        return 0.0

    def get_button(self, button_name: str) -> bool:
        for button in self.buttons:
            if button.key_name == button_name:
                return button.is_pressed
        return False
