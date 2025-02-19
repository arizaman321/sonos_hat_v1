import json
import RPi.GPIO as GPIO
#from RPi_GPIO_Rotary import rotary
#from rotary_dev import Rotary
from functools import partial
from soco import SoCo
from soco.exceptions import SoCoException
from gpiozero import RotaryEncoder, Button
import itertools
from time import sleep
import signal
import sys
#GPIO.setwarnings(False)

#REV2
VOL_ENCODER1 = {
    'CLK': 9,
    'DT': 0,
    'SW': 10
}
BASS_ENCODER2 = {
    'CLK': 12,
    'DT': 5,
    'SW': 6
}
TREBLE_ENCODER3 = {
    'CLK': 26,
    'DT': 21,
    'SW': 11
}
EXTRA_ENCODER4 = {
    'CLK': 1,
    'DT': 20,
    'SW': 7
}

SPEAKER_SELECT_SW = 23
ROOM_SELECT_SW = 22
ALL_ROOMS_SW = 13
SINGLE_ROOM_SW = 16 
SINGLE_SPK_SW = 19 



MODE_LEDS = {
    "all_rooms_mode" : 24,
    "single_room_mode" : 8,
    "single_speaker_mode" : 25
}

ROOM_LEDS = {
    "LIV": 2, 
    "KIT": 14, 
    "BED": 17, 
    "OFF": 27
}

##REV1
# VOL_ENCODER1 = {
#     'CLK': 4,
#     'DT': 3,
#     'SW': 2
# }
# BASS_ENCODER2 = {
#     'CLK': 21,
#     'DT': 20,
#     'SW': 16
# }
# TREBLE_ENCODER3 = {
#     'CLK': 22,
#     'DT': 27,
#     'SW': 17
# }
# EXTRA_ENCODER4 = {
#     'CLK': 18,
#     'DT': 15,
#     'SW': 14
# }

# SPEAKER_SELECT_SW = 1
# ROOM_SELECT_SW = 12
# ALL_ROOMS_SW = 25
# SINGLE_ROOM_SW = 8
# SINGLE_SPK_SW = 7



# MODE_LEDS = {
#     "all_rooms_mode" : 10,
#     "single_room_mode" : 9,
#     "single_speaker_mode" : 11
# }

# ROOM_LEDS = {
#     "LIV": 19, 
#     "KIT": 26, 
#     "BED": 23, 
#     "OFF": 24
# }



BUTTONS_UP= [VOL_ENCODER1['SW'],BASS_ENCODER2['SW'],TREBLE_ENCODER3['SW'],EXTRA_ENCODER4['SW']]
BUTTONS_DOWN = [SPEAKER_SELECT_SW,ROOM_SELECT_SW,ALL_ROOMS_SW,SINGLE_ROOM_SW,SINGLE_SPK_SW]
GPIO.setmode(GPIO.BCM)
# for pin in range(0,28):
#     #pin = MODE_LEDS[LED]
#     GPIO.setup(pin, GPIO.OUT)
#     GPIO.output(pin,GPIO.LOW)


SPK_LEDS = [3,4,15,18]
#SPK_LEDS = [0,5,6,13]
ALL_LED_PINS = []
for pin in SPK_LEDS:
    ALL_LED_PINS.append(pin)
for pin in ROOM_LEDS:
    ALL_LED_PINS.append(ROOM_LEDS[pin])
for pin in MODE_LEDS:
    ALL_LED_PINS.append(MODE_LEDS[pin])


#btn = Button(SPEAKER_SELECT_SW)

ENCODERS_CONFIG = [VOL_ENCODER1, BASS_ENCODER2, TREBLE_ENCODER3, EXTRA_ENCODER4]

encoder_assignments = ['MISSING', 'MISSING', 'MISSING', 'MISSING']

UPDATE_LEDS = 1

ZONES = ["CENTER", "LEFT", "RIGHT", "ANY"]

MODES = ["all_rooms_mode", "single_room_mode", "single_speaker_mode"]
current_mode = MODES[2]

VOL_STEP = 5

SPEAKER_SELECT = 1

ROOMS = ["LIV", "KIT", "BED", "OFF"]
ROOMS_CYCLIC = itertools.cycle(ROOMS)
for i in range(2): 
    current_room = next(ROOMS_CYCLIC) #ROOMS[1]
# current_zone = ZONES[0]


# Load the configuration file


def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Initialize encoders based on the configuration


def initialize_encoders():
    encoders = []
    # Initialize (clk,dt,sw,ticks)
    for idx, encoder_name in enumerate(ENCODERS_CONFIG):
        #encoder = Rotary(encoder_name['CLK'], encoder_name['DT'], encoder_name['SW'])
        
        encoder = RotaryEncoder(encoder_name['DT'],encoder_name['CLK'])
        encoders.append(encoder)

    return encoders


def register_encoder_turn():
    global encoders
    for idx, encoder in enumerate(encoders):
        # encoder.register(
        #     increment=partial(
        #         STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'DOWN'),
        #     decrement=partial(
        #         STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'UP')
        # )
    
        encoder.when_rotated_clockwise = partial(STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'UP')
        encoder.when_rotated_counter_clockwise = partial(STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'DOWN')
        #print(encoder)


def  assign_encoders_speakers():
    global encoder_assignments
    if current_mode == 'all_rooms_mode':
        # print(config)
        for i in range(len(encoder_assignments)):
            encoder_assignments[i] = ['MISSING']
        for encoder_idx, encoder in enumerate(config['room_encoders']):
            encoder_speakers = config['room_encoders'][encoder]
            if len(list(encoder_speakers.keys())) > 0:
                encoder_speaker = encoder_speakers[list(
                    encoder_speakers.keys())[0]]
                if encoder_idx >= 3:
                    encoder_assignments[3][0] = get_speaker_group(encoder_speaker['IP'])
                else:
                    encoder_assignments[encoder_idx][0] = get_speaker_group(encoder_speaker['IP'])

    elif current_mode == 'single_room_mode':
        for i in range(len(encoder_assignments)):
            encoder_assignments[i] = ['MISSING']
        room_idx = ROOMS.index(current_room)
        config_room_name = list(config['room_encoders'].keys())[room_idx]
        encoder_speakers = config['room_encoders'][config_room_name]
        for speaker in encoder_speakers:
            encoder_speaker = encoder_speakers[speaker]
            speaker_idx = ZONES.index(encoder_speaker['Zone'])
            if encoder_assignments[speaker_idx][0] == 'MISSING':
                encoder_assignments[speaker_idx][0] = get_speaker(encoder_speaker['IP'])
            else:
                encoder_assignments[speaker_idx].append(
                    get_speaker(encoder_speaker['IP']))

    elif current_mode == 'single_speaker_mode':
        for i in range(len(encoder_assignments)):
            encoder_assignments[i] = ['MISSING']
        room_idx = ROOMS.index(current_room)
        config_room_name = list(config['room_encoders'].keys())[room_idx]
        encoder_speakers = config['room_encoders'][config_room_name]
        for speaker in encoder_speakers:
            encoder_speaker = encoder_speakers[speaker]
            if encoder_speaker['Speaker Encoder'] == SPEAKER_SELECT :#and SPEAKER_SELECT < len(list(encoder_speakers.keys())):
                temp_speaker = get_speaker(encoder_speaker['IP'])
                for i in range(len(['VOL', 'BASS', 'TREB'])):
                    if encoder_assignments[i][0] == 'MISSING':
                        encoder_assignments[i][0] = temp_speaker
                    else:
                        encoder_assignments[i].append(temp_speaker)
                break
    
    print_encoders()
    #print(encoder_assignments)
    # for i,encoder in enumerate(encoder_assignments):
    #     for item in encoder:
    #         for sub in item:
    #             if item == 'MISSING':
    #                 print(f'Encoder {i+1} - Player MISSING')
    #             else:
    #                 try:
    #                     print(f'Encoder {i+1} - Player {sub.player_name}')
    #                 except:
    #                     try:
    #                         print(f'Encoder {i+1} - Player {sub.label}')
    #                     except:
    #                         print(f'Encoder {i+1} - Player MISSING')

def get_speaker(speaker_ip):

    try:
        # Connect to the speaker by IP address
        speaker = SoCo(speaker_ip)

        # Verify the connection
        if not speaker:
            #TODO Try to find by player name
            print(f"Unable to connect to speaker with IP {speaker_ip}.")
            speaker = 'MISSING'

        return speaker

    except SoCoException as e:
        print(f"An error occurred: {e}")
        return 'MISSING'


def get_speaker_group(speaker_ip):
    try:
        # Connect to the speaker by IP address
        speaker = SoCo(speaker_ip)

        # Verify the connection
        if not speaker:
            print(f"Unable to connect to speaker with IP {speaker_ip}.")
            group = 'MISSING'

        # Get the group the speaker belongs to
        group = speaker.group
        if not group:
            print(f"Speaker at IP {speaker_ip} is not part of a group.")
            group = speaker

        return group

    except SoCoException as e:
        print(f"An error occurred: {e}")
        return 'MISSING'

    except:
        return 'MISSING'


def change_volume(devices, direction="UP",single=False, step = VOL_STEP):
    if single == True:
        devices = [SoCo(devices[0])]
        
    if current_mode == 'all_rooms_mode':
        if devices[0] != 'MISSING':
            try:
                device = devices[0]
                if direction == 'UP':
                    device.set_relative_volume(step)
                elif direction == 'DOWN':
                    device.set_relative_volume(-step)
                print(f'Changed {device} volume {direction} by {step}.')
            except SoCoException as e:
                print(f"An error occurred: {e}")
            except:
                print(f'ERROR Changing {device} volume {direction} by {step}.')
    else:
        for device in devices:
            if device != 'MISSING':
                try:
                    if direction == 'UP':
                        device.volume += step
                    elif direction == 'DOWN':
                        device.volume -= step
                    print(f'Changed {device} volume {direction} by {step}.')
                except SoCoException as e:
                    print(f"An error occurred: {e}")
                    continue
                except:
                    print(f'ERROR Changing {device} volume {direction} by {step}.')
    

def change_bass(devices, direction="UP",single=False):
    if single == True:
        devices = [SoCo(devices[0])]
    for device in devices:
        if device != 'MISSING':
            try:
                if direction == 'UP':
                    device.bass += 1
                elif direction == 'DOWN':
                    device.bass -= 1
            except SoCoException as e:
                print(f"An error occurred: {e}")
                continue
            except:
                print(f'ERROR Changing {device} bass {direction}.')


def change_treble(devices, direction="UP"):
    for device in devices:
        if device != 'MISSING':
            try:
                if direction == 'UP':
                    device.treble += 1
                elif direction == 'DOWN':
                    device.treble -= 1
            except SoCoException as e:
                print(f"An error occurred: {e}")
                continue
            except:
                print(f'ERROR Changing {device} bass {direction}.')
        # TODO add code that will search for missing device

def button_callback(channel):
    #print('hi')
    print('button pressed, ',channel)
    if channel in [ALL_ROOMS_SW, SINGLE_SPK_SW, SINGLE_ROOM_SW]:
       # print(current_mode)
        change_mode(channel)
    elif channel == ROOM_SELECT_SW and current_mode not in ['all_rooms_mode']:
        change_room()
    elif channel == SPEAKER_SELECT_SW and current_mode in ['single_speaker_mode']:
        change_speaker()
        
def change_speaker():
    global SPEAKER_SELECT
    prev_spk = SPEAKER_SELECT
    SPEAKER_SELECT += 1
    room_idx = ROOMS.index(current_room)
    config_room_name = list(config['room_encoders'].keys())[room_idx]
    encoder_speakers = config['room_encoders'][config_room_name]
    #TODO - make speaker cyclic
    if SPEAKER_SELECT > len(list(encoder_speakers.keys())) or SPEAKER_SELECT > 4:
        SPEAKER_SELECT = 1
    update_encoders()
    if UPDATE_LEDS: update_LEDs()
    print(f'Speaker changed from {prev_spk} to {SPEAKER_SELECT}')
    #print('herree')

def change_room():
    global current_room, SPEAKER_SELECT
    prev_room = current_room
    SPEAKER_SELECT = 1
    current_room = next(ROOMS_CYCLIC)
    update_encoders()
    if UPDATE_LEDS: update_LEDs()
    print(f'Room changed from {prev_room} to {current_room}')

def change_mode(channel):
    global current_mode, SPEAKER_SELECT
    prev_mode = current_mode
    if channel == ALL_ROOMS_SW:
        current_mode = MODES[MODES.index('all_rooms_mode')]
    elif channel == SINGLE_SPK_SW:
        current_mode = MODES[MODES.index('single_speaker_mode')]
    elif channel == SINGLE_ROOM_SW:
        #change_volume(['192.168.10.52'],single=True)
        current_mode = MODES[MODES.index('single_room_mode')]
    else:
        current_mode = current_mode
    SPEAKER_SELECT = 1
    update_encoders()
    if UPDATE_LEDS: update_LEDs()
    print(f'Mode changed from {prev_mode} to {current_mode}')
    #print('here')
    #return current_mode

def LED_on_off(dir = 'off'):
    for pin in ALL_LED_PINS:
        GPIO.output(pin,GPIO.LOW)
        
    for pin in ALL_LED_PINS:
        if dir == 'on':
            GPIO.output(pin,GPIO.HIGH)

def LED_flash(repeat = 1, time = .25):
    for i in range(repeat):
        LED_on_off(dir = 'on')
        sleep(time)
        LED_on_off('off')
    
def LED_cycle(repeat=1,time = .15):
    for i in range(repeat):
        for pin in ALL_LED_PINS:
            GPIO.output(pin,GPIO.LOW)
        for pin in ALL_LED_PINS:
            GPIO.output(pin,GPIO.HIGH)
            sleep(time)
            GPIO.output(pin,GPIO.LOW)
        

def update_LEDs():
    
    mode_turn_on_pin = -1
    for mode in MODE_LEDS:
        if current_mode == mode:
            mode_turn_on_pin = MODE_LEDS[mode]
        else:
            off_pin = MODE_LEDS[mode]
            GPIO.output(off_pin,GPIO.LOW)

    
    room_turn_on_pin = -1
    for room in ROOM_LEDS:
        if current_room == room and current_mode not in ['all_rooms_mode']:
            room_turn_on_pin = ROOM_LEDS[room]
        else:
            off_pin = ROOM_LEDS[room]
            GPIO.output(off_pin,GPIO.LOW)
    
    speaker_turn_on_pins = [-1,-1,-1,-1]
    val = SPEAKER_SELECT - 1 
    if val > 3 and current_mode not in ['all_rooms_mode','single_room_mode']:
        speaker_turn_on_pins[3] = 1
    else:
        if current_mode not in ['all_rooms_mode','single_room_mode']:
            speaker_turn_on_pins[val] = 1
    for idx,pin in enumerate(speaker_turn_on_pins):
        if pin == 1:
            GPIO.output(SPK_LEDS[idx], GPIO.HIGH)    
        else:
            GPIO.output(SPK_LEDS[idx], GPIO.LOW)  

    if mode_turn_on_pin >= 0:
        GPIO.output(mode_turn_on_pin, GPIO.HIGH)
    if room_turn_on_pin >= 0:
        GPIO.output(room_turn_on_pin, GPIO.HIGH)
    # for idx,pin in enumerate(speaker_turn_on_pins):
    #     if pin:
    #         GPIO.output(SPK_LEDS[idx], GPIO.HIGH)
    #print(speaker_turn_on_pins)
    
    

def update_encoders():
    assign_encoders_speakers()
    register_encoder_turn()

def startup_test():
    # global current_mode, current_room, SPEAKER_SELECT
    # temp_mode = current_mode
    # temp_room = current_room
    # temp_spk = SPEAKER_SELECT
    try:
        for mode in [23,22,13]:
            change_mode(mode)
            for room in ROOMS:
                if mode != 23:
                    change_room()
                for i in range(1,5):
                    if mode not in [23,13]:
                        change_speaker()
                        print(f'mode - {mode} / room - {room} / speaker - {i}') 
                        sleep(.1)  
        # current_mode = temp_mode
        # current_room = temp_room
        # SPEAKER_SELECT = temp_spk
        return 1
    except:
        return 0

def handle_exit(signum, frame):
    """
    This function is called when you press Ctrl+C or send a kill signal.
    Cleans up GPIO and exits gracefully.
    """
    print("\nExiting program...")
    GPIO.cleanup()
    sys.exit(0)

def print_encoders():

    for i in range(0,4):
        curr_enc = encoder_assignments[i]
        if encoder_assignments[i] == ['MISSING']:
            print(f'Encoder {i+1} : MISSING')
        else:
            if current_mode == 'all_rooms_mode':
                print(f'Encoder {i+1} : {encoder_assignments[i][0].label}')
            else:
                print(f'Encoder {i+1} : {encoder_assignments[i][0].player_name}')

STATIC_TURN_FUNCTIONS = {
    'all_rooms_mode': [change_volume, change_volume, change_volume, change_volume],
    'single_room_mode': [change_volume, change_volume, change_volume, change_volume],
    'single_speaker_mode': [change_volume, change_bass, change_treble, change_volume]
}

# buttons_dict = {}

for button_pin in BUTTONS_UP:
    # GPIO.setup(button_pin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    # GPIO.add_event_detect(button_pin,GPIO.RISING,callback=partial(button_callback), bouncetime=200)
    button = Button(button_pin)
    button.when_pressed = button_callback
for button_pin in BUTTONS_DOWN:
    GPIO.setup(button_pin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(button_pin,GPIO.RISING,callback=partial(button_callback), bouncetime=200)



if __name__ == "__main__":

    for LED in MODE_LEDS:
        pin = MODE_LEDS[LED]
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin,GPIO.LOW)
    for LED in ROOM_LEDS:
        pin = ROOM_LEDS[LED]
        GPIO.setup(pin, GPIO.OUT)
        GPIO.output(pin,GPIO.LOW)
    for LED_pin in SPK_LEDS:
        GPIO.setup(LED_pin, GPIO.OUT)
        GPIO.output(LED_pin,GPIO.LOW)   
    

    
    config_path = "sonos_config.json"
    config = load_config(config_path)

    encoders = initialize_encoders()
    # for enc in encoders:
    #     enc.start()
    update_encoders()
    # for i in range(10):
    #     change_room()
    #     print(current_room)
    #change_mode(current_mode,13)
    #change_volume(encoder_assignments[0], 'DOWN')

    #change_speaker()
    #change_volume(encoder_assignments[0], 'DOWN')
    
    temp_mode = current_mode
    temp_room = current_room
    temp_spk = SPEAKER_SELECT   

    #initialize_sucess = startup_test()
    current_mode = temp_mode
    current_room = temp_room
    SPEAKER_SELECT = temp_spk   
    #update_encoders()
    LED_flash()
    LED_cycle()
    if UPDATE_LEDS: update_LEDs()


    try:
        print("System is running. Press Ctrl+C to exit.")
        while True:
            #print(current_mode)
            pass
    except KeyboardInterrupt:
        for pin in ALL_LED_PINS:
            GPIO.output(pin,GPIO.LOW)
        print("Exiting...")
    finally:
        for pin in ALL_LED_PINS:
            GPIO.output(pin,GPIO.LOW)
        GPIO.cleanup()
    
    # # Handle SIGINT (Ctrl+C) or SIGTERM to exit gracefully
    # signal.signal(signal.SIGINT, handle_exit)
    # signal.signal(signal.SIGTERM, handle_exit)
    # print("Press the button or Ctrl+C to exit.")
    
    # # Instead of 'while True:', just pause and wait for signals (or GPIO events)
    # signal.pause()
