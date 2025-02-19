# from RPi import GPIO
# import threading, time

# class Rotary:

#     def setup(self):
#         GPIO.setmode(GPIO.BCM)
#         GPIO.setup(self.pins['clk'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
#         GPIO.setup(self.pins['dt'], GPIO.IN, pull_up_down=GPIO.PUD_UP)
#         GPIO.setup(self.pins['sw'], GPIO.IN, pull_up_down=GPIO.PUD_UP)

#     def __init__(self,clk = None,dt = None,sw = None, tick = 2, bounce=1000):
#         if clk == None or dt == None or sw == None:
#             raise BaseException("Invalid Configuration: CLK, DT and SW must be specified")
#         self.pins = {"clk":clk,"dt":dt,"sw":sw}
#         self.ticks = tick
#         self.bounce = bounce
#         self.increment, self.decrement, self.switched, self.changed = None,None,None,None
#         self.setup()


#     def register(self, **params):
#         if 'increment' in params:
#             self.increment= params['increment']
#         if 'decrement' in params:
#             self.decrement = params['decrement']
#         if 'pressed' in params:
#             self.switched = params['pressed']
#         if 'onchange' in params:
#             self.changed= params['onchange'] 


#     def watch(self, stop_event):
#         clkLastState = GPIO.input(self.pins['clk'])
#         counter = 0
#         tick = 1
#         pressed = 0
#         while not stop_event.is_set():
#             clkState = GPIO.input(self.pins['clk'])
#             dtState = GPIO.input(self.pins['dt'])
#             swState = GPIO.input(self.pins['sw'])
            
#             if swState == 0:
#                 if pressed < int( (time.time()*1000)-self.bounce ):
#                     if self.switched is not None:
#                         pressed = int(time.time() * 1000)
#                         self.switched()
#             if clkState != clkLastState:
#                 if tick == self.ticks:
#                     tick =1
#                     if dtState != clkState:
#                             counter += 1
#                             if self.increment is not None:
#                                 self.increment()
#                     elif dtState == clkState:
#                             counter -= 1
#                             if self.decrement is not None:
#                                 self.decrement()
#                     if self.changed is not None:
#                         self.changed(counter)
#                 else:
#                     tick += 1
#             clkLastState = clkState
#             time.sleep(0.0015)

#     def start(self):
#         self.stop_event = threading.Event()
#         self.th = threading.Thread(target=self.watch, args=[self.stop_event])
#         self.th.setDaemon(True)
#         self.th.start()
    
#     def stop(self):
#         self.stop_event.set()

# def up():
#     print('up')
    
# def down():
#     print('down')
# obj3 = Rotary(0,9,10,2)
# obj3.register(increment=up, decrement=down)
# obj3.register(pressed=up)
# #GPIO.setup(4, GPIO.OUT, initial = GPIO.HIGH)
# obj3.start()

# while True:
#     pass

#!/usr/bin/env python3
import RPi.GPIO as GPIO
import threading
import time

class RotaryEncoder(threading.Thread):
    """
    RotaryEncoder reads a rotary encoder (with CLK and DT pins) and an optional push button
    in a separate thread. It supports separate callback functions for increment (clockwise)
    and decrement (counter-clockwise) events.

    Args:
        clk (int): GPIO pin number for the CLK signal.
        dt (int): GPIO pin number for the DT signal.
        encoder_increment_callback (function, optional): Function to call when the encoder
            rotates clockwise. It will be passed the new position as the first argument.
        encoder_increment_callback_args (tuple, optional): Additional arguments for the increment callback.
        encoder_decrement_callback (function, optional): Function to call when the encoder
            rotates counter-clockwise. It will be passed the new position as the first argument.
        encoder_decrement_callback_args (tuple, optional): Additional arguments for the decrement callback.
        debounce_time (float, optional): Minimum time between encoder counts (in seconds) to help debounce.
        button_pin (int, optional): GPIO pin number for the push-button switch.
        button_callback (function, optional): Function to call when the button is pressed.
        button_callback_args (tuple, optional): Additional arguments to pass to the button callback.
        button_debounce_time (float, optional): Minimum time between button events (in seconds) to debounce.

    Attributes:
        position (int): Current position counter (increments or decrements with rotation).
    """
    def __init__(self, clk, dt,
                 encoder_increment_callback=None,
                 encoder_increment_callback_args=(),
                 encoder_decrement_callback=None,
                 encoder_decrement_callback_args=(),
                 debounce_time=0.01,
                 button_pin=None,
                 button_callback=None,
                 button_callback_args=(),
                 button_debounce_time=0.01):
        threading.Thread.__init__(self)
        self.clk = clk
        self.dt = dt

        # Encoder callbacks and their arguments.
        self.encoder_increment_callback = encoder_increment_callback
        self.encoder_increment_callback_args = encoder_increment_callback_args
        self.encoder_decrement_callback = encoder_decrement_callback
        self.encoder_decrement_callback_args = encoder_decrement_callback_args
        self.debounce_time = debounce_time
        self.last_event_time = time.time()

        # Button callback and its arguments.
        self.button_pin = button_pin
        self.button_callback = button_callback
        self.button_callback_args = button_callback_args
        self.button_debounce_time = button_debounce_time
        self.last_button_event_time = time.time()

        self.position = 0
        self._running = True

        # Setup GPIO using BCM numbering.
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.clk, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.dt, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        
        # Initialize CLK state.
        self.last_clk_state = GPIO.input(self.clk)

        # Setup button if provided.
        if self.button_pin is not None:
            GPIO.setup(self.button_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
            self.last_button_state = GPIO.input(self.button_pin)
    
    def update_encoder_increment_callback(self, callback, callback_args=()):
        """
        Update the encoder increment callback and its arguments on the fly.
        """
        self.encoder_increment_callback = callback
        self.encoder_increment_callback_args = callback_args

    def update_encoder_decrement_callback(self, callback, callback_args=()):
        """
        Update the encoder decrement callback and its arguments on the fly.
        """
        self.encoder_decrement_callback = callback
        self.encoder_decrement_callback_args = callback_args

    def update_button_callback(self, callback, callback_args=()):
        """
        Update the button callback and its arguments on the fly.
        """
        self.button_callback = callback
        self.button_callback_args = callback_args

    def run(self):
        """
        Continuously polls the encoder pins and (if provided) the button pin.
        It updates the position on the falling edge of CLK and triggers the corresponding callback:
          - For a clockwise (increment) event, it calls the encoder_increment_callback.
          - For a counter-clockwise (decrement) event, it calls the encoder_decrement_callback.
        It also triggers the button callback on a falling edge (button press) after debouncing.
        """
        while self._running:
            current_time = time.time()

            # ----- Encoder handling -----
            current_clk_state = GPIO.input(self.clk)
            if self.last_clk_state == GPIO.HIGH and current_clk_state == GPIO.LOW:
                if (current_time - self.last_event_time) >= self.debounce_time:
                    self.last_event_time = current_time
                    # Determine rotation direction.
                    if GPIO.input(self.dt) == GPIO.HIGH:
                        # Clockwise rotation.
                        self.position += 1
                        if self.encoder_increment_callback:
                            self.encoder_increment_callback(self.position, *self.encoder_increment_callback_args)
                    else:
                        # Counter-clockwise rotation.
                        self.position -= 1
                        if self.encoder_decrement_callback:
                            self.encoder_decrement_callback(self.position, *self.encoder_decrement_callback_args)
            self.last_clk_state = current_clk_state

            # ----- Button handling -----
            if self.button_pin is not None:
                current_button_state = GPIO.input(self.button_pin)
                # Detect falling edge for button press (assuming active-low).
                if self.last_button_state == GPIO.HIGH and current_button_state == GPIO.LOW:
                    if (current_time - self.last_button_event_time) >= self.button_debounce_time:
                        self.last_button_event_time = current_time
                        if self.button_callback:
                            self.button_callback(*self.button_callback_args)
                self.last_button_state = current_button_state

            # Small delay to reduce CPU usage.
            time.sleep(0.001)
    
    def stop(self):
        """
        Stops the encoder thread and performs GPIO cleanup.
        """
        self._running = False
        self.join()
        GPIO.cleanup()


# Test the library if run as a script.
if __name__ == '__main__':
    def inc_callback(position,pass_var):
        print("Increment callback. New position:", position)
        print(pass_var)

    def dec_callback(position):
        print("Decrement callback. New position:", position)

    def button_callback():
        print("Button pressed!")
        new_str='POP'
        encoder.update_encoder_increment_callback(inc_callback,("POP",))

    # Define GPIO pins.
    CLK_PIN = 0
    DT_PIN = 9
    BUTTON_PIN = 10

    encoder = RotaryEncoder(
        clk=CLK_PIN,
        dt=DT_PIN,
        encoder_increment_callback=inc_callback,
        encoder_increment_callback_args=('LOL',),
        encoder_decrement_callback=dec_callback,
        encoder_decrement_callback_args=(),
        debounce_time=0.05,
        button_pin=BUTTON_PIN,
        button_callback=button_callback,
        button_callback_args=(),
        button_debounce_time=0.05
    )
    encoder.start()
    
    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Stopping encoder...")
        encoder.stop()
