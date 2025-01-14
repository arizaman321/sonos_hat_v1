"""Entry point for sonos_hat_v1."""

#from sonos_hat_v1.cli import main  # pragma: no cover

#from sonos_hat_v1.configure_gui import run_gui
import sys
from configure_gui import run_gui
if __name__ == "__main__":
    #print(sys.path)

    run_gui()
