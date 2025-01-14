import soco

def run_gui():
	
	devices = soco.discover()
	print(devices)
