import os
import logging
import json
import re
from datetime import datetime
from enum import IntEnum

from faustrollctl.common.utils import run_command, get_application_pid
from faustrollctl.common.constants import RC_OK, RC_BAD, PANMUPHLECTL_PATH

logger = logging.getLogger(__name__)

OBSIDIAN_VAULT_PATH = os.path.expanduser("~/documents/by_category/vault")

########################################################
# Utilities
########################################################

def find_obsidian_node(id, state, node=None):
    if node == None:
        start_node = {"children": [ state['main'], state['left'], state['right'] ]}
        return find_obsidian_node(id, state, node=start_node)
    
    if "id" in node and node["id"] == id:
        return node
    
    if "children" in node:
        for c in node["children"]:
            r = find_obsidian_node(id, state, c)

            if r != None:
                return r
    
    return None

def obsidian_append_content(file_path, content):
    content_lines = content.split('\n')

    with open(file_path, "r") as file:
        write_idx = 0
        file_lines = file.read().split('\n')
        
        # For a "Project" file we always want to append
        # before the tasks section at the end. For a "Note"
        # file we always want to append before the references
        # section at the end.
        for i in range(0,len(file_lines)):
            line = file_lines[i]

            if "**Tasks:**" in line:
                write_idx = i - 2
                break
        
            if "**References**" in line:
                write_idx = i - 2
                break
        
        if write_idx == 0:
            write_idx = len(file_lines) - 1
        
        file_lines[write_idx:write_idx] = content_lines
    
    with open(file_path, "w") as file:
        file.write('\n'.join(file_lines))

def obsidian_get_active_file():
    rc = RC_OK
    with open(os.path.join(OBSIDIAN_VAULT_PATH, ".obsidian/workspace.json"), "r") as j_file:
        obsidian_state = json.loads(j_file.read())
    
    active_id = obsidian_state['active']
    active_node = find_obsidian_node(active_id, obsidian_state)

    if not active_node:
        return [RC_BAD, None]
    
    file_name = active_node['state']['state']['file']

    return [RC_OK, file_name]

def obsidian_get_sections(file_path):
    logger.info(f"Getting section of file {file_path}")
    rc = RC_OK
    note_sections = []

    with open(file_path, "r") as md_file:
        file_lines = md_file.readlines()
        cur_section = []

        for line in file_lines:
            # It's really this simple
            if line[0] == '#':
                logger.debug(line)
                note_sections.append(cur_section.copy())
                cur_section[:] = []
            
            cur_section.append(line)
        note_sections.append(cur_section.copy())
    
    return [rc, note_sections]

def obsidian_write_sections(sections, file_path):
    logger.info(f"Writing sections to file {file_path}")
    rc = RC_OK

    lines = progress_section = [item for sublist in sections for item in sublist]

    with open(file_path, "w") as md_file:
        md_file.writelines(lines)
    
    return rc

# This function is not working right now because a down/up arrow press doesn't
# correspond 1-1 with text file lines
def obsidian_set_cursor_position(line, total_lines=-1):
    # Put cursor at beginning of line
    rc, _ = run_command(["/usr/bin/wtype", "-P", "home", "-p", "home"])
    
    if total_lines != -1 and line > (total_lines / 2):
        # Set cursor to end of file
        rc, _ = run_command(["/usr/bin/wtype", "-M", "ctrl", "-P", "end", "-p", "end", "-m", "ctrl"])

        lines_upwards = total_lines - line
        print(lines_upwards)

        for i in range(0,lines_upwards):
            rc, _ = run_command(["/usr/bin/wtype", "-P", "home", "-p", "home"])
            rc, _ = run_command(["/usr/bin/wtype", "-M", "ctrl", "-P", "up", "-p", "up", "-m", "ctrl"])
    else:
        # Set cursor to start of file
        rc, stdout = run_command(["/usr/bin/wtype", "-M", "ctrl", "-P", "home", "-p", "home", "-m", "ctrl"])

        for i in range(0,line):
            rc, _ = run_command(["/usr/bin/wtype", "-P", "home", "-p", "home"])
            rc, _ = run_command(["/usr/bin/wtype", "-M", "ctrl", "-P", "down", "-p", "down", "-m", "ctrl"])
    
    # Put cursor at beginning of line
    rc, _ = run_command(["/usr/bin/wtype", "-P", "home", "-p", "home"])

    return rc

########################################################
# Knowledge Management
########################################################

def switch_to_obsidian():
    rc = RC_OK

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
    
    return rc

def quote_to_obsidian(clip_content, cite_content):
    rc = RC_OK

    # # Open note selector
    # run_command(["/usr/bin/wtype", "-M", "ctrl", "o"])
    rc, active_file = obsidian_get_active_file()

    if rc != RC_OK:
        logger.warning("Error getting active obsidian file")
        return rc

    active_path = os.path.join(OBSIDIAN_VAULT_PATH, active_file)

    quote_content = clip_content.rstrip('\n').replace('\n', '\n> ')
    quote_content = f"\n >{quote_content} s"

    if cite_content:
        pass

    rc = obsidian_append_content(active_path, quote_content)

    return rc

def obsidian_create_date_entry():
    rc = RC_OK
    rc, active_file = obsidian_get_active_file()

    if rc != RC_OK:
        logger.warning("Error getting active obsidian file")
        return [rc, None]

    active_path = os.path.join(OBSIDIAN_VAULT_PATH, active_file)
    
    rc, notes_sections = obsidian_get_sections(active_path)

    progress_idx, progress_subsections = __get_progress_subsections(notes_sections)

    if progress_idx == -1 and progress_subsections == None:
        logger.info(f"Unable to find progress section in note {active_file}")
        return RC_OK

    cur_date = datetime.today()
    new_entry = False
    entry_idx = -1
    for i in range(len(progress_subsections)-1,0,-1):
        if len(progress_subsections[i]) < 1:
            logger.warning("Encountered progress entry less than 1 line long")
        
        if progress_subsections[i][0].startswith("**Tasks:**"):
            entry_idx = i - 1
            break
    
    if entry_idx == 0:
        new_entry = True
    else:
        prev_entry_date = __entry_string_to_date(progress_subsections[entry_idx][0])

        # Check if the date of the previous entry was not today
        if cur_date.date() != prev_entry_date.date():
            new_entry = True
    
    # Add an entry for today's date
    if new_entry:
        new_entry_string = __entry_date_to_string(cur_date)
        target_subsection = progress_subsections[entry_idx]

        # If this subsection containers at least a previous header
        if len(target_subsection) >= 2:
            # Make sure the previous section ends on a newline before
            # the line break
            if target_subsection[-2] != '\n':
                target_subsection[-1].insert("\n")

            insert_pos = -1
        else:
            # TODO: we could adjust the header of the previous day since nothing was
            #       written there. For now, just assume it is the beginning of the
            #       progress section
            insert_pos = -1

        target_subsection.insert(insert_pos,new_entry_string)
        target_subsection.insert(insert_pos,"\n")
        target_subsection.insert(insert_pos,"\n")

    # Flatten down the progress section
    progress_section = [item for sublist in progress_subsections for item in sublist]

    # Update the main sections
    notes_sections[progress_idx] = progress_section

    # Write it back
    rc = obsidian_write_sections(notes_sections, active_path)

    # Set the cursor
    # note_length = __get_sections_length(notes_sections)
    # entry_pos = __get_sections_length(notes_sections[:entry_idx+1])
    # entry_pos = entry_pos - 3 # Backup 3 lines for the line break and newline

    switch_to_obsidian()
    # obsidian_set_cursor_position(entry_pos, total_lines=note_length)

    return rc

def obsidian_select_note():
    rc = RC_OK

    rc = switch_to_obsidian()

    if rc != RC_OK:
        logger.warning("Failed switching to obsidian")
        return RC_BAD
    
    rc, _ = run_command(["/usr/bin/wtype", "-M", "ctrl", "-P", "O", "-p", "O", "-m", "ctrl"])

    return rc

def __entry_string_to_date(date_string):
    # Remove Markdown bold syntax '**' and suffixes
    date_string = date_string.strip().strip('*').strip()
    
    # Regular expression to match and remove only ordinal suffixes from the day part
    date_string = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', date_string)
    
    # Determine if the string contains a year
    if ',' in date_string:
        # If a year is included
        format_str = "%B %d, %Y"
    else:
        # If no year is included, assume the current year
        format_str = "%B %d, %Y"
        date_string += f", {datetime.now().year}"
    
    # Create a datetime object from the string
    date_obj = datetime.strptime(date_string, format_str)
    
    return date_obj

def __entry_date_to_string(date_obj):
    # Determine the correct ordinal suffix
    day = date_obj.day
    if 10 <= day % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    
    # Format the datetime object to the desired string format
    formatted_str = f"**{date_obj.strftime('%B %d')}{suffix}**\n"
    
    return formatted_str

def __get_sections_length(sections):
    total_len = 0

    for section in sections:
        total_len = total_len + len(section)
    
    return total_len
########################################################
# Project Management
########################################################

def obsidian_get_projects():
    logger.info(f"Getting projects")
    rc = RC_OK
    projects_list = []

    projects_path = os.path.join(OBSIDIAN_VAULT_PATH, "projects")

    if not os.path.exists(projects_path):
        logger.warning(f"Unable to locate projects path at {projects_path}")
        return [ RC_BAD, None ]

    projects_list = os.listdir(projects_path)
    projects_list = [ project_file.split('.')[0] for project_file in projects_list ]
    projects_list.sort()

    return [RC_OK, projects_list]

def obsidian_get_active_project():
    logger.info("Getting active obsidian project")
    rc, active_file = obsidian_get_active_file()
    active_subdir, active_filename = active_file.split('/')

    if active_subdir == "projects":
        return [RC_OK, active_filename.split(".")[0]]
    
    return [RC_OK, None]

def __get_progress_subsections(sections):
    subsections = []
    progress_section = None
    progress_idx = -1

    for section in sections:
        if "# Progress" in section[0]:
            progress_section = section
            progress_idx = sections.index(progress_section)
            break
    
    if not progress_section:
        return [-1, None]
    
    cur_section = []
    for line in progress_section:

        if line.startswith("**") and (line.endswith("**\n") or line.endswith("** \n")):
            logger.debug(f"{line}")
            subsections.append(cur_section.copy())
            cur_section[:] = []
            
        cur_section.append(line)
    subsections.append(cur_section.copy())
    
    return progress_idx, subsections


########################################################
# Task Management
########################################################

class TaskStatus(IntEnum):
    TODO = 0
    IN_PROGRESS = 1
    DONE = 2
    CANCELLED = 3

def obsidian_get_tasks(project_name):
    logger.info(f"Getting tasks for project {project_name}")
    rc = RC_OK
    task_strings = []
    task_objects = []

    projects_path = os.path.join(OBSIDIAN_VAULT_PATH, "projects")

    if not os.path.exists(projects_path):
        logger.warning(f"Unable to locate projects path at {projects_path}")
        return [ RC_BAD, None ]
    
    project_path = os.path.join(projects_path, f"{project_name}.md")

    if not os.path.exists(project_path):
        logger.warning(f"Unable to find project with name {project_name} at path {project_path}")
    
    logger.info(f"Reading tasks for project {project_name} from file at path {project_path}")
    with open(project_path, "r") as project_file:
        tasks_idx = 0
        file_lines = project_file.read().split('\n')
        
        # For a "Project" file we always want to append
        # before the tasks section at the end. For a "Note"
        # file we always want to append before the references
        # section at the end.
        for i in range(0,len(file_lines)):
            line = file_lines[i]

            if "**Tasks:**" in line:
                logger.debug(f"Found tasks section on line {i}")
                tasks_idx = i
                break

        if tasks_idx == 0:
            logger.warning(f"Unable to locate tasks section in file {project_path}")
            return [RC_BAD, None]

        if tasks_idx == len(file_lines) -1:
            logger.info(f"No tasks found")
            return [RC_OK, []]

        task_strings = file_lines[tasks_idx+1:]
    
    for task_string in task_strings:
        task_obj = __task_string_to_dict(task_string)

        if task_obj == None:
            logger.warning(f"Failed to parse task string '{task_string}'")
        else:
            task_objects.append(task_obj)


    return [RC_OK, task_objects]

def obsidian_insert_task(project_name, task_obj):
    task_string = __task_dict_to_string(task_obj)

    project_path = os.path.join(OBSIDIAN_VAULT_PATH, f"projects/{project_name}.md")

    with open(project_path, "r") as project_file:
        project_lines = project_file.readlines()
    
    for i in range(0,len(project_lines)):
        line = project_lines[i]

        if "**Tasks:**" in line:
            project_lines.insert(i+1, f"{task_string}\n")
            break
    
    with open(project_path, "w") as project_file:
        project_file.writelines(project_lines)
    
    return RC_OK

def obsidian_modify_task(project_name, task_obj):
    task_string = __task_dict_to_string(task_obj)
    project_path = os.path.join(OBSIDIAN_VAULT_PATH, f"projects/{project_name}.md")

    with open(project_path, "r") as project_file:
        project_lines = project_file.readlines()
    
    for i in range(0,len(project_lines)):
        line = project_lines[i]

        if task_obj["description"] in line:
            lpad = line.split('-')[0]
            project_lines[i] = f"{lpad}{task_string}\n"
            break
        
    with open(project_path, "w") as project_file:
        project_file.writelines(project_lines)
    
    return RC_OK

def obsidian_remove_task(project_name, task_obj):
    task_string = __task_dict_to_string(task_obj)
    project_path = os.path.join(OBSIDIAN_VAULT_PATH, f"projects/{project_name}.md")

    with open(project_path, "r") as project_file:
        project_lines = project_file.readlines()
    
    for i in range(0,len(project_lines)):
        line = project_lines[i]

        if task_obj["description"] in line and '#task' in line:
            project_lines.pop(i)
            break
        
    with open(project_path, "w") as project_file:
        project_file.writelines(project_lines)
    
    return RC_OK


__task_date_format = "%Y-%m-%d"

"""
    Todo Example:
        - [ ] #task create a hotkey that copies text from the current selection and pastes it as a quote in obsidian ➕ 2024-08-06
    In-Progress Example:
        - [/] #task create a hotkey that copies text from the current selection and pastes it as a quote in obsidian ➕ 2024-08-06
    Done Example:
        - [x] #task create a hotkey that copies text from the current selection and pastes it as a quote in obsidian ➕ 2024-08-06 ✅ 2024-08-14
    Cancelled Example:    
        - [-] #task create a hotkey that copies text from the current selection and pastes it as a quote in obsidian ➕ 2024-08-06 ❌ 2024-08-14 
"""
def __task_string_to_dict(task_string):
    # Define regex patterns for each form
    patterns = {
        TaskStatus.TODO: r'\[ \] #task (.*?) ➕ (\d{4}-\d{2}-\d{2})',
        TaskStatus.IN_PROGRESS: r'\[\/\] #task (.*?) ➕ (\d{4}-\d{2}-\d{2})',
        TaskStatus.DONE: r'\[x\] #task (.*?) ➕ (\d{4}-\d{2}-\d{2}) ✅ (\d{4}-\d{2}-\d{2})',
        TaskStatus.CANCELLED: r'\[-\] #task (.*?) ➕ (\d{4}-\d{2}-\d{2}) ❌ (\d{4}-\d{2}-\d{2})'
    }

    # Iterate through the patterns and try to match the input string
    for status, pattern in patterns.items():
        match = re.search(pattern, task_string)
        if match:
            if status in [TaskStatus.DONE, TaskStatus.CANCELLED]:
                description, start_date, end_date = match.groups()
                return {
                    'status': status,
                    'description': description,
                    'start_date': datetime.strptime(start_date, __task_date_format),
                    'end_date': datetime.strptime(end_date, __task_date_format)
                }
            else:
                description, start_date = match.groups()
                return {
                    'status': status,
                    'description': description,
                    'start_date': datetime.strptime(start_date, __task_date_format)
                }

    return None

def __task_dict_to_string(task_obj):
    """
    Recreate the task string from a task object.
    
    :param task_obj: A dictionary representing the task, with keys:
                     - 'status': The status of the task ('todo', 'in-progress', 'done', 'cancelled')
                     - 'description': The description of the task
                     - 'start_date': The start date of the task
                     - 'end_date': The end date of the task (optional, for 'done' and 'cancelled')
    :return: A string representing the task in its original format
    """
    status_map = {
        TaskStatus.TODO: '[ ]',
        TaskStatus.IN_PROGRESS: '[/]',
        TaskStatus.DONE: '[x]',
        TaskStatus.CANCELLED: '[-]'
    }
    
    # Extract information from the task object
    status = task_obj.get('status')
    description = task_obj.get('description')
    start_date = task_obj.get('start_date')
    end_date = task_obj.get('end_date')
    
    # Convert dates to strings
    if start_date != None:
        start_date = datetime.strftime(start_date, __task_date_format)
    else:
        start_date = datetime.strftime(datetime.today(), __task_date_format)

    if end_date != None:
        end_date = datetime.strftime(end_date, __task_date_format)
    else:
        end_date = datetime.strftime(datetime.today(), __task_date_format)

    # Determine the correct status symbol
    status_symbol = status_map.get(status, '[ ]')
    
    # Construct the task string based on the status
    if int(status) == int(TaskStatus.DONE):
        return f"- {status_symbol} #task {description} ➕ {start_date} ✅ {end_date}"
    elif int(status) == int(TaskStatus.CANCELLED):
        return f"- {status_symbol} #task {description} ➕ {start_date} ❌ {end_date}"
    else:
        return f"- {status_symbol} #task {description} ➕ {start_date}"