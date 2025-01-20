import json
import RPi.GPIO as GPIO
#from RPi_GPIO_Rotary import rotary
from rotary_dev import Rotary
from functools import partial
from soco import SoCo
from soco.exceptions import SoCoException
#from gpiozero import RotaryEncoder, Button
import itertools

#GPIO.setwarnings(False)
VOL_ENCODER1 = {
    'CLK': 0,
    'DT': 9,
    'SW': 10
}
BASS_ENCODER2 = {
    'CLK': 5,
    'DT': 12,
    'SW': 6
}
TREBLE_ENCODER3 = {
    'CLK': 21,
    'DT': 26,
    'SW': 11
}
EXTRA_ENCODER4 = {
    'CLK': 20,
    'DT': 1,
    'SW': 7
}

SPEAKER_SELECT_SW = 16
ROOM_SELECT_SW = 19
ALL_ROOMS_SW = 23
SINGLE_ROOM_SW = 13
SINGLE_SPK_SW = 22

BUTTONS = [VOL_ENCODER1['SW'],BASS_ENCODER2['SW'],TREBLE_ENCODER3['SW'],EXTRA_ENCODER4['SW'],SPEAKER_SELECT_SW,ROOM_SELECT_SW,ALL_ROOMS_SW,SINGLE_ROOM_SW,SINGLE_SPK_SW]

MODE_LEDS = {
    "all_rooms_mode" : 23,
    "single_room_mode" : 8,
    "single_speaker_mode" : 25
}

ROOM_LEDS = {
    "LIV": 2, 
    "KIT": 14, 
    "BED": 17, 
    "OFF": 27
}

SPK_LEDS = [3,4,15,18]

GPIO.setmode(GPIO.BCM)
#btn = Button(SPEAKER_SELECT_SW)

ENCODERS_CONFIG = [VOL_ENCODER1, BASS_ENCODER2, TREBLE_ENCODER3, EXTRA_ENCODER4]

encoder_assignments = ['MISSING', 'MISSING', 'MISSING', 'MISSING']

ROOMS = ["LIV", "KIT", "BED", "OFF"]
ROOMS_CYCLIC = itertools.cycle(ROOMS)

ZONES = ["CENTER", "LEFT", "RIGHT", "ANY"]

MODES = ["all_rooms_mode", "single_room_mode", "single_speaker_mode"]


SPEAKER_SELECT = 1

for i in range(1): 
    current_room = next(ROOMS_CYCLIC) #ROOMS[1]
# current_zone = ZONES[0]
current_mode = MODES[2]

# Load the configuration file


def load_config(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Initialize encoders based on the configuration


def initialize_encoders():
    encoders = []
    # Initialize (clk,dt,sw,ticks)
    for idx, encoder_name in enumerate(ENCODERS_CONFIG):
        encoder = Rotary(encoder_name['CLK'], encoder_name['DT'], encoder_name['SW'])
        
        #encoder = RotaryEncoder(encoder_name['CLK'],encoder_name['DT'])
        encoders.append(encoder)

    return encoders


def register_encoder_turn():
    global encoders
    for idx, encoder in enumerate(encoders):
        encoder.register(
            increment=partial(
                STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'UP'),
            decrement=partial(
                STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'DOWN')
        )
        
        # encoder.when_rotated_clockwise = partial(STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'UP')
        # encoder.when_rotated_counter_clockwise = partial(STATIC_TURN_FUNCTIONS[current_mode][idx], encoder_assignments[idx], 'DOWN')
        print(encoder)


def assign_encoders_speakers():
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
                    encoder_assignments[3][0] = [
                        get_speaker_group(encoder_speaker['IP'])]
                else:
                    encoder_assignments[encoder_idx][0] = [
                        get_speaker_group(encoder_speaker['IP'])]

    if current_mode == 'single_room_mode':
        for i in range(len(encoder_assignments)):
            encoder_assignments[i] = ['MISSING']
        room_idx = ROOMS.index(current_room)
        config_room_name = list(config['room_encoders'].keys())[room_idx]
        encoder_speakers = config['room_encoders'][config_room_name]
        for speaker in encoder_speakers:
            encoder_speaker = encoder_speakers[speaker]
            speaker_idx = ZONES.index(encoder_speaker['Zone'])
            if encoder_assignments[speaker_idx][0] == 'MISSING':
                encoder_assignments[speaker_idx][0] = [
                    get_speaker(encoder_speaker['IP'])]
            else:
                encoder_assignments[speaker_idx].append(
                    get_speaker(encoder_speaker['IP']))

    if current_mode == 'single_speaker_mode':
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
                        encoder_assignments[i][0] = [temp_speaker]
                    else:
                        encoder_assignments[i].append([temp_speaker])
                break


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


def change_volume(devices, direction="UP",single=False):
    if single == True:
        devices = [SoCo(devices[0])]
    for device in devices:
        if device != 'MISSING':
            try:
                if direction == 'UP':
                    device.volume += 5
                elif direction == 'DOWN':
                    device.volume -= 5
            except SoCoException as e:
                print(f"An error occurred: {e}")
                continue


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


def change_treble(devices, direction="UP"):
    for device in devices:
        if device != 'MISSING':
            try:
                if direction == 'UP':
                    device.treble += 1
                elif direction == 'DOWN':
                    device.treble -= 1
            except:
                continue
        # TODO add code that will search for missing device

def button_callback(channel):
    #print('hi')
    
    if channel in [ALL_ROOMS_SW, SINGLE_SPK_SW, SINGLE_ROOM_SW]:
       # print(current_mode)
        change_mode(channel)
    elif channel == ROOM_SELECT_SW and current_mode not in ['all_rooms_mode']:
        change_room()
    elif channel == SPEAKER_SELECT_SW and current_mode in ['single_speaker_mode']:
        change_speaker()
        
def change_speaker():
    global SPEAKER_SELECT
    SPEAKER_SELECT += 1
    room_idx = ROOMS.index(current_room)
    config_room_name = list(config['room_encoders'].keys())[room_idx]
    encoder_speakers = config['room_encoders'][config_room_name]
    #TODO - make speaker cyclic
    if SPEAKER_SELECT > len(list(encoder_speakers.keys())) or SPEAKER_SELECT > 4:
        SPEAKER_SELECT = 1
    update_encoders()
    print('herree')

def change_room():
    global current_room, SPEAKER_SELECT
    SPEAKER_SELECT = 1
    current_room = next(ROOMS_CYCLIC)
    update_encoders()

def change_mode(channel):
    global current_mode, SPEAKER_SELECT
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
    #print('here')
    #return current_mode
    
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
    if val > 3:
        speaker_turn_on_pins[3] = 1
    else:
        speaker_turn_on_pins[val] = 1
    for idx,pin in enumerate(speaker_turn_on_pins):
        if pin == -1:
            GPIO.output(SPK_LEDS[idx], GPIO.HIGH)    

    if mode_turn_on_pin >= 0:
        GPIO.output(mode_turn_on_pin, GPIO.HIGH)
    if room_turn_on_pin >= 0:
        GPIO.output(room_turn_on_pin, GPIO.HIGH)
    for idx,pin in enumerate(speaker_turn_on_pins):
        if pin:
            GPIO.output(SPK_LEDS[idx], GPIO.HIGH)
    print(speaker_turn_on_pins)
    
    

def update_encoders():
    assign_encoders_speakers()
    register_encoder_turn()

STATIC_TURN_FUNCTIONS = {
    'all_rooms_mode': [change_volume, change_volume, change_volume, change_volume],
    'single_room_mode': [change_volume, change_volume, change_volume, change_volume],
    'single_speaker_mode': [change_volume, change_bass, change_treble, change_volume]
}

# buttons_dict = {}

for button_pin in BUTTONS:
    GPIO.setup(button_pin,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
    GPIO.add_event_detect(button_pin,GPIO.RISING,callback=partial(button_callback))
    # buttons_dict[button_pin] = Button(button_pin)
    # buttons_dict[button_pin].when_pressed = button_callback
    
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

if __name__ == "__main__":

    config_path = "sonos_config.json"
    config = load_config(config_path)

    encoders = initialize_encoders()
    update_encoders()
    # for i in range(10):
    #     change_room()
    #     print(current_room)
    #change_mode(current_mode,13)
    #change_volume(encoder_assignments[1], 'DOWN')
    #change_speaker()
    for i in range(1,8):
        SPEAKER_SELECT = i
        update_LEDs()
    #change_speaker()
    try:
        print("System is running. Press Ctrl+C to exit.")
        while True:
            #print(current_mode)
            pass
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
