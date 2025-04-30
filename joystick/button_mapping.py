from .joystick import JoystickHandler


class ButtonMap:
    def __init__(self):
        self.joystick_handler = JoystickHandler()

        #initializes control variables with default values.
        self.deadzone: int = 5
        self.weight: int = 0
        self.for_backward: int = 0
        self.left_right: int = 0
        self.up_down: int = 0
        self.yaw: int = 0

        self.commands: list[str] = []

    def get_joystick_values(self) -> list[str]:
        if not self.joystick_handler.joystick:
            return

        self.commands = []

        #Gets joystick values
        x, y, z, buttons = self.joystick_handler.get_values()

        #Calculates base weight
        self.weight = (-z + 1) * 50

        #Calculates forward_backwards input
        self.for_backward = x * self.weight
        self.for_backward = (
            0
            if -self.deadzone < self.for_backward < self.deadzone
            else self.for_backward
        )

        #Calculates left_right input
        self.left_right = y * -1 * self.weight
        self.left_right = (
            0 if -self.deadzone < self.left_right < self.deadzone else self.left_right
        )

        self.up_down = 0
        self.yaw = 0

        #Process through a list of mapped buttons
        for button_key, button_value in buttons.items():
            if not button_value:
                continue
            match button_key:
                case 1:
                    self.commands.append("flip f")
                case 2:
                    self.up_down -= self.weight
                case 3:
                    self.up_down += self.weight
                case 4:
                    self.yaw -= self.weight
                case 5:
                    self.yaw += self.weight
                case 6:
                    self.commands.append("reboot")
                case 8:
                    self.commands.append("takeoff")
                case 9:
                    self.commands.append("land")
                case _:
                    self.commands.append("emergency")

        self.commands.append(
            f"rc {self.for_backward:.2f} {self.left_right:.2f} {self.up_down} {self.yaw}"
        )

        return self.commands
