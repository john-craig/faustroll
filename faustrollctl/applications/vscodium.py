import os
import logging
import json

from faustrollctl.common.constants import RC_OK, RC_BAD
from faustrollctl.common.utils import run_command, get_application_pid

logger = logging.getLogger(__name__)

VSCODIUM_CONFIG_PATH = os.path.expanduser("~/.config/VSCodium")

def vscodium_get_workspace():
    rc = RC_OK
    workspace = None

    rc, stdout = run_command(["/usr/bin/hyprctl", "activewindow", "-j"])
    active_window = json.loads(stdout)

    vscodium_active = active_window["initialTitle"] == "VSCodium"
    logger.info(f"VSCodium {"is" if vscodium_active else "is not"} the current window")

    with open(os.path.join(VSCODIUM_CONFIG_PATH, "User/globalStorage/storage.json"), "r") as j_file:
        vscodium_state = json.loads(j_file.read())

    if "lastActiveWindow" in vscodium_state["windowsState"]:
        last_window = vscodium_state["windowsState"]["lastActiveWindow"]
    else:
        logger.warning("No last active window found for VSCodium")
        return [RC_OK, None]

    if not vscodium_active:
        if "folder" in last_window:
            workspace = last_window["folder"]
        else:
            logger.warning("No folder found for last active window in VSCodium")
            return [RC_OK, None]
    else:
        if "openedWindows" in vscodium_state["windowsState"]:
            open_windows = vscodium_state["windowsState"]["openedWindows"]

            if len(open_windows) == 0:
                if "folder" in last_window:
                    workspace = last_window["folder"]

            for open_window in open_windows:
                if "folder" in open_window:
                    workspace_subfolder = open_window["folder"].split('/')[-1]

                    if workspace_subfolder in active_window['title']:
                        workspace = open_window["folder"]
                        break
                
            if not workspace:
                logger.warning("Did not find Hyprland active window among VSCodium active windows")
        else:
            logger.warning("No opened windows found in VSCodium")
            return [RC_OK, None]

    return [RC_OK, workspace]