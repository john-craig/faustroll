import os
import logging
import time
from enum import Enum

from faustrollctl.common.constants import RC_OK, RC_BAD, PANMUPHLECTL_PATH, STATE_DIR
from faustrollctl.common.utils import run_command, get_application_pid, merge_selector_cache, update_selector_cache
from faustrollctl.common.selector import Selector

from faustrollctl.functions.tasks import select_task, create_task, modify_task, remove_task

from obsidian_utils.projects import obsidian_get_projects
from faustrollctl.applications.vscodium import vscodium_get_workspace

project_cache_path = os.path.join(STATE_DIR, "projects.txt")

logger = logging.getLogger(__name__)

def select_project():
    rc, projects_list = obsidian_get_projects()
    projects_list = merge_selector_cache(projects_list, 
        project_cache_path)

    if rc != RC_OK:
        logger.warning("Error getting projects list")
        return (rc, None)
    
    rc, sel_project = Selector.select_from_list(projects_list)

    if rc != RC_OK:
        return (rc, None)

    update_selector_cache(sel_project, project_cache_path)

    return (rc, sel_project)

def get_projects_list():
    return obsidian_get_projects()

def get_active_project():
    return vscodium_get_workspace()

##########################################
# Project/Task Management
##########################################
def create_project_task():
    logger.info("Creating project task")
    rc, project_name = select_project()

    if rc != RC_OK:
        logger.warning("Error selecting project name")

    rc = create_task(project_name)

def modify_project_task():
    rc, project_name = select_project()

    if rc != RC_OK:
        logger.warning("Error selecting project name")
        return RC_BAD
    
    return modify_task(project_name)

def remove_project_task():
    rc, project_name = select_project()

    if rc != RC_OK:
        logger.warning("Error selecting project name")
        return RC_BAD
    
    return remove_task(project_name)