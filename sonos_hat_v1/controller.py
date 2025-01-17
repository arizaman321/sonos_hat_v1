#import Encoder
from configure_gui import load_rooms_from_file
from configure_gui import discover_and_load_speakers

##LOAD JSON
rooms = load_rooms_from_file()
print(rooms)
##DEFINE ENCODERS/BUTTONS
ENCODER1 = {
    'SW_PIN' : 12,
    'CLK_PIN' : 13,
    'DT_PIN' : 14,
    'Speakers' : [],
    'Sections' : []
}

ENCODER2 = {
    'SW_PIN' : 12,
    'CLK_PIN' : 13,
    'DT_PIN' : 14,
    'Speakers' : [],
    'Sections' : []
}

ENCODER3 = {
    'SW_PIN' : 12,
    'CLK_PIN' : 13,
    'DT_PIN' : 14,
    'Speakers' : [],
    'Sections' : []
}

ENCODER4 = {
    'SW_PIN' : 12,
    'CLK_PIN' : 13,
    'DT_PIN' : 14,
    'Speakers' : [],
    'Sections' : []
}

ENCODERS = [ENCODER1,ENCODER2,ENCODER3,ENCODER4]
SECTION_TEMPLATE = {
    'Speakers' : None,
    'Sections' : {
        "F" : None,
        "F" : None,
        "F" : None,
        "F" : None,
    }
}
SECTIONS = []
speakers_on_network = discover_and_load_speakers()

# if not speakers_on_network:
## File to save the speaker configuration

