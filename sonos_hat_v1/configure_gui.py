import json
import soco
import PySimpleGUI as sg

class Speaker:
    def __init__(self, name, ip_address, uid, volume, is_coordinator, group_members, knob=None, room=None, section=None):
        self.name = name
        self.ip_address = ip_address
        self.uid = uid
        self.volume = volume
        self.is_coordinator = is_coordinator
        self.group_members = group_members
        self.knob = knob
        self.room = room
        self.section = section

    def to_dict(self):
        return {
            "name": self.name,
            "ip_address": self.ip_address,
            "uid": self.uid,
            "volume": self.volume,
            "is_coordinator": self.is_coordinator,
            "group_members": self.group_members,
            "knob": self.knob,
            "room": self.room,
            "section": self.section
        }

    @staticmethod
    def from_dict(data):
        return Speaker(
            name=data["name"],
            ip_address=data["ip_address"],
            uid=data["uid"],
            volume=data["volume"],
            is_coordinator=data["is_coordinator"],
            group_members=data.get("group_members", []),
            knob=data.get("knob"),
            room=data.get("room"),
            section=data.get("section")
        )

    def __repr__(self):
        return (f"Speaker(name={self.name}, ip_address={self.ip_address}, uid={self.uid}, "
                f"volume={self.volume}, is_coordinator={self.is_coordinator}, "
                f"group_members={self.group_members}, knob={self.knob}, room={self.room}, section={self.section})")

class Room:
    def __init__(self, name, speakers, clk_pin=None, dt_pin=None, sw_pin=None):
        self.name = name
        self.speakers = speakers
        self.clk_pin = clk_pin
        self.dt_pin = dt_pin
        self.sw_pin = sw_pin

    def to_dict(self):
        return {
            "name": self.name,
            "speakers": [speaker.to_dict() for speaker in self.speakers],
            "clk_pin": self.clk_pin,
            "dt_pin": self.dt_pin,
            "sw_pin": self.sw_pin
        }

    @staticmethod
    def from_dict(data):
        return Room(
            name=data["name"],
            speakers=[Speaker.from_dict(s) for s in data["speakers"]],
            clk_pin=data.get("clk_pin"),
            dt_pin=data.get("dt_pin"),
            sw_pin=data.get("sw_pin")
        )

    def __repr__(self):
        return (f"Room(name={self.name}, speakers={self.speakers}, clk_pin={self.clk_pin}, "
                f"dt_pin={self.dt_pin}, sw_pin={self.sw_pin})")

# Function to discover and load speakers
def discover_and_load_speakers():
    print("Discovering Sonos devices...")
    devices = soco.discover()

    if not devices:
        print("No Sonos devices found on the network.")
        return []

    speakers = []
    for device in devices:
        # Get group members
        group = device.group
        group_members = [member.player_name for member in group.members] if group else []

        speaker = Speaker(
            name=device.player_name,
            ip_address=device.ip_address,
            uid=device.uid,
            volume=device.volume,
            is_coordinator=device.is_coordinator,
            group_members=group_members
        )

        speakers.append(speaker)

    return speakers

# Save rooms to a JSON file
def save_rooms_to_file(rooms, filename="rooms.json"):
    with open(filename, "w") as file:
        json.dump([room.to_dict() for room in rooms], file, indent=4)

# Load rooms from a JSON file
def load_rooms_from_file(filename="rooms.json"):
    try:
        with open(filename, "r") as file:
            data = json.load(file)
            return [Room.from_dict(room) for room in data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# Organize speakers into rooms
def organize_into_rooms(speakers):
    rooms = []
    coordinators = {s.name: s for s in speakers if s.is_coordinator}

    for idx, (name, coordinator) in enumerate(coordinators.items(), start=1):
        room_name = name if idx <= 4 else f"Room-{idx}"
        room_speakers = [s for s in speakers if coordinator.name in s.group_members or s.name == coordinator.name]
        rooms.append(Room(name=room_name, speakers=room_speakers))

    return rooms

# Display speakers in a GUI
def display_gui():
    sg.theme("DarkBlue3")

    speakers = discover_and_load_speakers()
    rooms = organize_into_rooms(speakers)

    def create_pi_setup_tab():
        room_frames = []
        for room in rooms:
            room_layout = [
                [
                    sg.Text("CLK Pin:"), sg.Combo([1, 4, 5, 6], default_value=room.clk_pin or 1, size=(5, 1), key=f"CLK_{room.name}"),
                    sg.Text("DT Pin:"), sg.Combo([1, 4, 5, 6], default_value=room.dt_pin or 1, size=(5, 1), key=f"DT_{room.name}"),
                    sg.Text("SW Pin:"), sg.Combo([1, 4, 5, 6], default_value=room.sw_pin or 1, size=(5, 1), key=f"SW_{room.name}")
                ]
            ]

            for speaker in room.speakers:
                speaker_layout = [
                    sg.Text(speaker.name),
                    sg.Text("Knob:"), sg.Combo([1, 2, 3, 4], default_value=speaker.knob or 1, size=(5, 1), key=f"KNOB_{speaker.uid}"),
                    sg.Text("Section:"), sg.Combo([1, 2, 3, 4, 5], default_value=speaker.section or 1, size=(5, 1), key=f"SECTION_{speaker.uid}")
                ]
                room_layout.append([speaker_layout])

            room_frames.append(
                [sg.Frame(title=room.name, layout=room_layout)]
            )
        return room_frames

    tab_layout = [
        [sg.Column(create_pi_setup_tab(), scrollable=True, size=(900, 400))]
    ]

    layout = [
        [sg.TabGroup([
            [sg.Tab("PI SETUP", tab_layout)]
        ])],
        [sg.Button("Refresh", key="-REFRESH-"), sg.Button("Save", key="-SAVE-"), sg.Button("Exit")]
    ]

    window = sg.Window("Sonos Speaker Manager", layout, resizable=True, size=(950, 600))

    while True:
        event, values = window.read()

        if event in (sg.WINDOW_CLOSED, "Exit"):
            break

        if event == "-REFRESH-":
            speakers = discover_and_load_speakers()
            rooms = organize_into_rooms(speakers)
            window.close()
            display_gui()
            return

        if event == "-SAVE-":
            for room in rooms:
                room.clk_pin = values.get(f"CLK_{room.name}")
                room.dt_pin = values.get(f"DT_{room.name}")
                room.sw_pin = values.get(f"SW_{room.name}")
                for speaker in room.speakers:
                    speaker.knob = values.get(f"KNOB_{speaker.uid}")
                    speaker.section = values.get(f"SECTION_{speaker.uid}")
            save_rooms_to_file(rooms)

    window.close()
