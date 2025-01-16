#import Encoder
from configure_gui import load_rooms_from_file
from configure_gui import discover_and_load_speakers
import json
import os
from soco.discovery import discover
import PySimpleGUI as sg
from soco import SoCo
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

# File to save the speaker configuration
CONFIG_FILE = "sonos_config.json"

SMART_CONFIG_DONE = False

def discover_speakers():
    """Discover all Sonos speakers on the network."""
    speakers = discover()
    if speakers:
        return {speaker.player_name: {"ip": speaker.ip_address, "coordinator": speaker.group.coordinator.player_name} for speaker in speakers}
    return {}

def load_config():
    """Load speaker configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            return json.load(file)
    return {}

def save_config(config):
    """Save speaker configuration to JSON file."""
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file, indent=4)

def initialize_config():
    """Initialize the configuration with discovered speakers and default assignments."""
    speakers = discover_speakers()
    room_encoders = {f"Room Encoder {i+1}": {} for i in range(4)}

    if speakers:
        grouped_speakers = {name: info for name, info in speakers.items()}
        pending_speakers = list(grouped_speakers.keys())

        # Assign coordinators and their groups first
        while pending_speakers:
            for speaker in list(pending_speakers):
                coordinator = grouped_speakers[speaker]["coordinator"]

                if coordinator in room_encoders["Room Encoder 1"] or coordinator in room_encoders["Room Encoder 2"] or \
                   coordinator in room_encoders["Room Encoder 3"]:
                    # Coordinator is already assigned, place this speaker in the same room
                    for room in room_encoders:
                        if coordinator in room_encoders[room]:
                            speaker_encoder = len(room_encoders[room]) + 1
                            room_encoders[room][speaker] = {
                                "Speaker Encoder": min(speaker_encoder, 4),
                                "Zone": "ANY",
                                "IP": grouped_speakers[speaker]["ip"]
                            }
                            pending_speakers.remove(speaker)
                            break
                elif coordinator == speaker:
                    # Assign the coordinator to a room encoder
                    for room in room_encoders:
                        if not room_encoders[room]:
                            room_encoders[room][coordinator] = {
                                "Speaker Encoder": 1,
                                "Zone": "CENTER",
                                "IP": grouped_speakers[coordinator]["ip"]
                            }
                            pending_speakers.remove(speaker)
                            break

        # Place remaining speakers without their coordinators in Room Encoder 4
        for speaker in pending_speakers:
            room_encoders["Room Encoder 4"][speaker] = {
                "Speaker Encoder": len(room_encoders["Room Encoder 4"]) + 1,
                "Zone": "ANY",
                "IP": grouped_speakers[speaker]["ip"]
            }

    return {"speakers": speakers, "room_encoders": room_encoders}

def assign_zones(room_encoders):
    """Assign zones based on speaker names and group members."""
    for room, speakers in room_encoders.items():
        coordinator = next((speaker for speaker, props in speakers.items() if props["Speaker Encoder"] == 1), None)
        if not coordinator:
            continue

        for speaker, properties in speakers.items():
            name_lower = speaker.lower()
            if speaker == coordinator:
                continue  # Coordinator already has a zone
            elif "left" in name_lower:
                properties["Zone"] = "LEFT"
            elif "right" in name_lower:
                properties["Zone"] = "RIGHT"
            elif "center" in name_lower:
                properties["Zone"] = "CENTER"
            else:
                properties["Zone"] = "ANY"

def control_speaker_volume(config_file, speaker_name, volume):
    """Control the volume of a specific speaker using the JSON config file."""
    if os.path.exists(config_file):
        with open(config_file, "r") as file:
            config = json.load(file)

        speakers = config.get("speakers", {})
        if speaker_name in speakers:
            speaker_ip = speakers[speaker_name]["ip"]
            speaker = SoCo(speaker_ip)
            speaker.volume = volume
            print(f"Set volume of {speaker_name} to {volume}.")
        else:
            print(f"Speaker '{speaker_name}' not found in configuration.")
    else:
        print(f"Configuration file '{config_file}' not found.")

def reset_and_initialize_config():
    """Reset the configuration and perform smart initialization."""
    config = initialize_config()
    assign_zones(config["room_encoders"])
    save_config(config)
    return config

def main():
    global SMART_CONFIG_DONE

    # Load or initialize configuration
    if os.path.exists(CONFIG_FILE):
        config = load_config()
    else:
        config = initialize_config()
        assign_zones(config["room_encoders"])
        save_config(config)
        SMART_CONFIG_DONE = True

    speakers = config.get("speakers", {})
    room_encoders = config.get("room_encoders", {})

    # PySimpleGUI Layout
    layout = [
        [sg.Text("Available Speakers:")],
        [sg.Listbox(values=[
            f"{name} ({info['ip']}, Coordinator: {info['coordinator']}){' - NEW' if name not in [speaker for room in room_encoders.values() for speaker in room] else ''}" 
            for name, info in speakers.items()], size=(80, 15), key="-SPEAKER_LIST-", enable_events=True)],
        [sg.Button("Refresh Speakers"), sg.Button("Reset Config")],
        [sg.Text("Assign to Room Encoder:"), sg.Combo([f"Room Encoder {i+1}" for i in range(4)], key="-ROOM_ENCODER-", readonly=True)],
        [sg.Text("Speaker Encoder (1-4):"), sg.Spin([1, 2, 3, 4], initial_value=1, key="-SPEAKER_ENCODER-")],
        [sg.Text("Zone (CENTER, LEFT, RIGHT, ANY):"), sg.Combo(["CENTER", "LEFT", "RIGHT", "ANY"], default_value="ANY", key="-ZONE-")],
        [sg.Button("Assign"), sg.Button("Save"), sg.Button("Control Volume"), sg.Button("Exit")],
        [sg.Text("Room Encoder Assignments:")],
        [sg.Multiline(default_text=json.dumps(room_encoders, indent=4), size=(100, 20), key="-OUTPUT-", disabled=True)],
    ]

    window = sg.Window("Sonos Speaker Grouping", layout, resizable=True)

    while True:
        event, values = window.read()

        if event == sg.WINDOW_CLOSED or event == "Exit":
            break

        if event == "Refresh Speakers":
            speakers = discover_speakers()
            config["speakers"] = speakers
            window["-SPEAKER_LIST-"].update([
                f"{name} ({info['ip']}, Coordinator: {info['coordinator']}){' - NEW' if name not in [speaker for room in room_encoders.values() for speaker in room] else ''}" 
                for name, info in speakers.items()])

        if event == "Reset Config":
            config = reset_and_initialize_config()
            speakers = config.get("speakers", {})
            room_encoders = config.get("room_encoders", {})
            window["-OUTPUT-"].update(json.dumps(room_encoders, indent=4))
            window["-SPEAKER_LIST-"].update([
                f"{name} ({info['ip']}, Coordinator: {info['coordinator']}){' - NEW' if name not in [speaker for room in room_encoders.values() for speaker in room] else ''}" 
                for name, info in speakers.items()])

        if event == "Assign":
            selected_speaker = values["-SPEAKER_LIST-"]
            room_encoder = values["-ROOM_ENCODER-"]
            speaker_encoder = values["-SPEAKER_ENCODER-"]
            zone = values["-ZONE-"]

            if not selected_speaker or not room_encoder:
                sg.popup("Please select a speaker and a room encoder.")
                continue

            # Extract speaker name from listbox entry
            selected_speaker_name = selected_speaker[0].split(" (")[0]

            # Ensure the speaker is only in one room encoder
            for room in room_encoders.values():
                if selected_speaker_name in room:
                    del room[selected_speaker_name]

            # Add speaker to the selected room encoder
            if room_encoder not in room_encoders:
                room_encoders[room_encoder] = {}

            room_encoders[room_encoder][selected_speaker_name] = {
                "Speaker Encoder": speaker_encoder,
                "Zone": zone,
                "IP": speakers[selected_speaker_name]["ip"]
            }

            # Update the output view
            window["-OUTPUT-"].update(json.dumps(room_encoders, indent=4))

        if event == "-SPEAKER_LIST-":
            selected_speaker = values["-SPEAKER_LIST-"]
            if selected_speaker:
                selected_speaker_name = selected_speaker[0].split(" (")[0]
                for room_name, room in room_encoders.items():
                    if selected_speaker_name in room:
                        speaker_config = room[selected_speaker_name]
                        window["-ROOM_ENCODER-"].update(value=room_name)
                        window["-SPEAKER_ENCODER-"].update(value=speaker_config["Speaker Encoder"])
                        window["-ZONE-"].update(value=speaker_config["Zone"])
                        break

        if event == "Save":
            # Save room encoders to config
            config["speakers"] = speakers
            config["room_encoders"] = room_encoders
            save_config(config)
            sg.popup("Configuration saved.")

        if event == "Control Volume":
            selected_speaker = values["-SPEAKER_LIST-"]
            if not selected_speaker:
                sg.popup("Please select a speaker to control.")
                continue

            selected_speaker_name = selected_speaker[0].split(" (")[0]
            volume = sg.popup_get_text("Enter volume (0-100):", "Control Volume")
            if volume and volume.isdigit() and 0 <= int(volume) <= 100:
                control_speaker_volume(CONFIG_FILE, selected_speaker_name, int(volume))
            else:
                sg.popup("Invalid volume value.")

    window.close()

if __name__ == "__main__":
    main()
