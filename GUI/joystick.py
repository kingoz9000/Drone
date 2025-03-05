import pyglet
import time


class JoystickHandler:
    def __init__(self, debug: bool = False):
        """Initialize Pyglet and detect the joystick."""
        self.joystick = None
        self.connect_joystick()

        if debug:
            pyglet.clock.schedule_interval(self.get_values, 0.05)  # Update every 50ms
            self.start_reading()

    def start_reading(self):
        if not self.joystick:
            print("No valid joystick found")
            return
        # Run Pyglet event loop
        pyglet.app.run()

    def connect_joystick(self) -> bool:
        """Find and connect to the first available joystick."""
        devices = pyglet.input.get_joysticks()

        if not devices:
            print("No joystick detected")
            return False

        self.joystick = devices[0]
        self.joystick.open()
        print(f"Connected to: {self.joystick.device.name}")

        # Attach event handlers for joystick input
        self.joystick.on_joybutton_press = self.on_joybutton_press
        self.joystick.on_joybutton_release = self.on_joybutton_release

        # Define button dictionary
        self.buttons: dict = {}
        return True

    def on_joybutton_press(self, joystick, button) -> None:
        """Handle button press."""
        self.buttons[button + 1] = True

    def on_joybutton_release(self, joystick, button) -> None:
        """Handle button release."""
        self.buttons[button + 1] = False

    def get_values(self, dt=0) -> tuple:
        """Update loop (called every 100ms)."""
        if dt != 0:
            print(self.joystick.x, self.joystick.y, self.joystick.z, self.buttons)

        return (self.joystick.x, self.joystick.y, self.joystick.z, self.buttons)


if __name__ == "__main__":
    JoystickHandler(debug=True)
