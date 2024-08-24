import subprocess
import logging
import json
import os

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

def get_selector_cache(cache_path):
    if not os.path.exists(cache_path):
        return []

    with open(cache_path, "r") as cache_file:
        selector_cache = cache_file.read().split('\n')
        print(f"Selector cache: {selector_cache}")
    
    return selector_cache

def merge_selector_cache(selector_list, cache_path):
    selector_cache = get_selector_cache(cache_path)
    
    merged_list = selector_list.copy()

    for item in selector_cache:
        if item in merged_list:
            merged_list.remove(item)
    
    merged_list = selector_cache.copy() + merged_list

    return merged_list

def update_selector_cache(item, cache_path):
    selector_cache = get_selector_cache(cache_path)

    if item in selector_cache:
        selector_cache.remove(item)
    
    selector_cache.insert(0, item)

    with open(cache_path, "w") as cache_file:
        cache_file.write("\n".join(selector_cache))