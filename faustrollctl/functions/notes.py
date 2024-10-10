import os
import logging
import time
from enum import Enum

from faustrollctl.common.constants import RC_OK, RC_BAD, PANMUPHLECTL_PATH
from faustrollctl.common.utils import run_command, get_application_pid
from obsidian_utils.knowledge import quote_to_obsidian, obsidian_select_note
from obsidian_utils.projects import obsidian_get_active_project, obsidian_add_status_entry
from faustrollctl.applications.chromium import cite_from_chromium

logger = logging.getLogger(__name__)

####################################
# Constants
####################################

class QuoteDest(Enum):
    NONE = 0
    OBSIDIAN = 1

class QuoteSrc(Enum):
    AUTO = 0
    CHROME = 1

QUOTE_FUNCTIONS = {
    QuoteDest.OBSIDIAN: quote_to_obsidian
}

CITE_FUNCTIONS = {
    QuoteSrc.CHROME: cite_from_chromium
}

####################################
# Utilities
####################################

def get_content_from_selection():
    # Get current contents of clipboard
    rc, stdout = run_command(["/usr/bin/wl-paste", "-p"])

    if rc != RC_OK:
        return [rc, None]

    return [rc, stdout]

####################################
# Quote Functions
####################################

def quote_from_selection(src_app, dest_app):
    rc = RC_OK

    if src_app in CITE_FUNCTIONS:
        cite_fn = CITE_FUNCTIONS[src_app]
    else:
        cite_fn = None

    if dest_app in QUOTE_FUNCTIONS:
        quote_fn = QUOTE_FUNCTIONS[dest_app]
    else:
        quote_fn = None

    rc, clip_content = get_content_from_selection()

    if rc != RC_OK:
        logger.warning("Failed getting selection content")
        return rc

    # Get current application PID
    rc, cur_app_pid = get_application_pid()

    if rc != RC_OK:
        return rc

    if cite_fn:
        rc, cite_content = cite_fn(cur_app_pid)

        if rc != RC_OK:
            return rc
    else:
        cite_content = None

    # Get note application PID
    rc, note_app_pid = get_application_pid(name="obsidian")
    
    if rc != RC_OK:
        return rc

    # Switch to note-taking application
    logger.info("Switching to note-taking application")
    rc, _ = run_command([PANMUPHLECTL_PATH, "switch-application", "--pid", str(note_app_pid)])
    
    if rc != RC_OK:
        logger.warning("Failed to switch to note-taking application")
        return rc

    # Add a bit of a delay, for UX
    time.sleep(0.5)

    if quote_fn:
        logger.info("Running quote hook")
        rc = quote_fn(clip_content, cite_content)
    else:
        rc, _ = run_command(["wl-paste", clip_content])
    
    logger.info("Switch back to original application")
    rc, _ = run_command([PANMUPHLECTL_PATH, "switch-application", "--pid", str(cur_app_pid)])

    if rc != RC_OK:
        logger.warning("Failed to switch back to original application")
        rc = RC_OK # Not a critical error

    return rc

def quote_to_obsidian_from_selection():
    logger.info("Quoting to Obsidian from Selection")

    return quote_from_selection(None, QuoteDest.OBSIDIAN)

####################################
# Note Management Functions
####################################
def create_date_entry():
    rc, active_project = obsidian_get_active_project()

    if rc != RC_OK:
        return rc

    if active_project is None:
        return RC_OK

    return obsidian_add_status_entry(active_project)

def select_note():
    return obsidian_select_note()