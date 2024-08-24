import subprocess
import json
import logging
import os
import time
import argparse

from faustrollctl.functions.notes import quote_to_obsidian_from_selection, create_date_entry, select_note
from faustrollctl.functions.projects import get_projects_list, select_project, get_active_project, create_project_task, modify_project_task, remove_project_task
from faustrollctl.functions.tasks import select_task
logger = logging.getLogger(__name__)

FAUSTROLLCTL_ACTIONS = {
    'quote-selection':     quote_to_obsidian_from_selection,

    'select-note':         select_note,
    'create-date-entry':   create_date_entry,

    'select-project':      select_project,
    'get-projects':        get_projects_list,
    'get-active-project':  get_active_project,

    'create-project-task': create_project_task,
    'modify-project-task': modify_project_task,
    'remove-project-task': remove_project_task

}

def main():
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(description="Panmuphle Control")
    parser.add_argument("action", choices=FAUSTROLLCTL_ACTIONS.keys())

    args = parser.parse_args()

    func = FAUSTROLLCTL_ACTIONS[args.action]

    rc = func()

    return rc

if __name__ == "__main__":
    main()
