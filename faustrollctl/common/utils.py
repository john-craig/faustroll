import subprocess
import logging
import json

from faustrollctl.common.constants import RC_OK, RC_BAD, PANMUPHLECTL_PATH

logger = logging.getLogger(__name__)

def run_command(command, input=None):
    logger.debug(f"Running command: {command}")
    p = subprocess.run(command, capture_output=True, text=True, input=input)

    if p.returncode:
        logger.warning(f"Command failed with RC {p.returncode}\n\tstdout: {p.stdout}\n\tstderr: {p.stderr}")
        return [p.returncode, None]

    return [p.returncode, p.stdout]

def get_application_pid(name=None, filter_fn=None):
    logger.info("Getting application PID")
    rc = RC_OK
    app_pid = None

    if name == None:
        rc, stdout = run_command(["/usr/bin/hyprctl", "activewindow", "-j"])

        if rc != RC_OK:
            logger.warning("Failed to get application PID for current application")
            return [rc, None]

        app = json.loads(stdout)
        app_pid = app['pid']
    else:
        # Obtain application info from panmuphle
        rc, stdout = run_command([PANMUPHLECTL_PATH, "find-applications", "--name", name])
        
        resp = json.loads(stdout)

        if resp["rc"] != RC_OK:
            logger.warning("There was an error finding applications")
            return [resp["rc"], None]

        found_apps = resp["applications"]

        if filter_fn:
            found_apps = [ app for app in found_apps if filter_fn(app, found_apps)]

        if len(found_apps) < 1:
            logger.warning(f"Unable to find application matching name {name}")
            return [RC_BAD, None]
        elif len(found_apps) > 1:
            logger.warning(f"Multiple applications matching {name} found, unable to uniquely identify")
            return [RC_BAD, None]
        
        app_pid = found_apps[0]['pid']
    
    return [rc, app_pid]
