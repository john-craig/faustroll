import os
import logging
import time
from enum import Enum

from faustrollctl.common.constants import RC_OK, RC_BAD, PANMUPHLECTL_PATH
from faustrollctl.common.utils import run_command, get_application_pid
from faustrollctl.common.selector import Selector

from faustrollctl.functions.tasks import select_task, create_task, modify_task, remove_task

from faustrollctl.applications.obsidian import obsidian_get_projects
from faustrollctl.applications.vscodium import vscodium_get_workspace

logger = logging.getLogger(__name__)

def select_project():
    rc, projects_list = obsidian_get_projects()

    if rc != RC_OK:
        logger.warning("Error getting projects list")
        return rc
    
    return Selector.select_from_list(projects_list)

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