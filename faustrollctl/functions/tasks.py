import os
import logging
import time

from faustrollctl.common.constants import RC_OK, RC_BAD, PANMUPHLECTL_PATH
from faustrollctl.common.utils import run_command, get_application_pid
from faustrollctl.common.selector import Selector

from faustrollctl.applications.obsidian import obsidian_get_tasks, obsidian_get_active_project, obsidian_insert_task, obsidian_modify_task, obsidian_remove_task, TaskStatus

logger = logging.getLogger(__name__)

def select_status():
    status_mapping = [ TaskStatus.TODO, TaskStatus.IN_PROGRESS, 
        TaskStatus.DONE, TaskStatus.CANCELLED ]
    statuses = [ "Todo", "In Progress", "Done", "Cancelled"]
    rc, sel_status = Selector.select_from_list(statuses, small=True)

    status_idx = statuses.index(sel_status)

    return (rc, status_mapping[status_idx])

def create_task(project_name):
    logger.info("Creating task")
    rc = RC_OK

    rc, task_desc = Selector.enter_text(small=True)

    if rc != RC_OK:
        return rc

    task_obj = {
        'status': TaskStatus.TODO,
        'description': task_desc
    }

    rc = obsidian_insert_task(project_name, task_obj)

    return rc

def modify_task(project_name):
    rc, task_obj = select_task(project_name, status_filter=[
        TaskStatus.TODO,
        TaskStatus.IN_PROGRESS
    ])

    if rc != RC_OK:
        return rc

    rc, new_status = select_status()

    if rc != RC_OK:
        return rc

    task_obj['status'] = new_status

    rc = obsidian_modify_task(project_name, task_obj)

    return rc

def remove_task(project_name):
    rc, task_obj = select_task(project_name)

    if rc != RC_OK:
        return rc

    rc = obsidian_remove_task(project_name, task_obj)

    return rc

def select_task(project_name=None, status_filter=[]):
    if project_name == None:
        rc, project_name = obsidian_get_active_project()

        if project_name == None:
            logger.warning("No active project found in obsidian")
            return [RC_OK, None]

    rc, task_list = get_task_list(project_name)

    if len(status_filter) != 0:
        task_list = [task_obj for task_obj in task_list if task_obj['status'] in status_filter]

    task_texts = [task_obj["description"] for task_obj in task_list]
    rc, sel_text = Selector.select_from_list(task_texts, small=True)

    sel_task = None

    for task_obj in task_list:
        if sel_text == task_obj["description"]:
            sel_task = task_obj
            break

    return [RC_OK, sel_task]

def get_task_list(project_name):
    return obsidian_get_tasks(project_name)

