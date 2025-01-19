import json
import RPi.GPIO as GPIO
#from RPi_GPIO_Rotary import rotary
from rotary_dev import Rotary
from functools import partial
from soco import SoCo
from soco.exceptions import SoCoException
from gpiozero import RotaryEncoder, Button


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
ROOM_SELECT_SW = 18
ALL_ROOMS_SW = 19
SINGLE_ROOM_SW = 20
SINGLE_SPK_SW = 21

BUTTONS = [VOL_ENCODER1]

GPIO.setmode(GPIO.BCM)
#btn = Button(SPEAKER_SELECT_SW)
btn = GPIO.setup(SPEAKER_SELECT_SW,GPIO.OUT,initial = GPIO.LOW)
ENCODERS_CONFIG = [VOL_ENCODER1, BASS_ENCODER2, TREBLE_ENCODER3, EXTRA_ENCODER4]

encoder_assignments = ['MISSING', 'MISSING', 'MISSING', 'MISSING']

ROOMS = ["LIV", "KIT", "BED", "OFF"]
ZONES = ["CENTER", "LEFT", "RIGHT", "ANY"]
MODES = ["all_rooms_mode", "single_room_mode", "single_speaker_mode"]
SPEAKER_SELECT = 1
current_room = ROOMS[1]
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
        
        # encoder = RotaryEncoder(27, 21)
        encoders.append(encoder)

    return encoders


def register_encoder_turn(encoders):
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


def assign_encoders_speakers(encoder_assignments):

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
            if encoder_speaker['Speaker Encoder'] == SPEAKER_SELECT:
                temp_speaker = get_speaker(encoder_speaker['IP'])
                for i in range(len(['VOL', 'BASS', 'TREB'])):
                    if encoder_assignments[i][0] == 'MISSING':
                        encoder_assignments[i][0] = [temp_speaker]
                    else:
                        encoder_assignments[i].append([temp_speaker])


def get_speaker(speaker_ip):

    try:
        # Connect to the speaker by IP address
        speaker = SoCo(speaker_ip)

        # Verify the connection
        if not speaker:
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


def change_volume(devices, direction="UP"):
    for device in devices:
        if device != 'MISSING':
            try:
                if direction == 'UP':
                    device.volume += 5
                elif direction == 'DOWN':
                    device.volume -= 5
            except:
                continue


def change_bass(devices, direction="UP"):
    for device in devices:
        if device != 'MISSING':
            try:
                if direction == 'UP':
                    device.bass += 1
                elif direction == 'DOWN':
                    device.bass -= 1
            except:
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


STATIC_TURN_FUNCTIONS = {
    'all_rooms_mode': [change_volume, change_volume, change_volume, change_volume],
    'single_room_mode': [change_volume, change_volume, change_volume, change_volume],
    'single_speaker_mode': [change_volume, change_bass, change_treble, change_volume]
}

if __name__ == "__main__":

    config_path = "sonos_config.json"
    config = load_config(config_path)

    encoders = initialize_encoders()
    assign_encoders_speakers(encoder_assignments)
    register_encoder_turn(encoders)

    change_volume(encoder_assignments[1], 'DOWN')

    try:
        print("System is running. Press Ctrl+C to exit.")
        while True:
            pass
    except KeyboardInterrupt:
        print("Exiting...")
    finally:
        GPIO.cleanup()
