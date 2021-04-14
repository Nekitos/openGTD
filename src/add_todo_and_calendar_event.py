#!/usr/bin/env python
import re
import os
from google_calendar_api import CalendarApi
import delete_done_event

TODO_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'To_do.md'))
BUYING_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Shopping_list.md'))

PATTERN_PROJECT_NAME = r'^### .*$'
PATTERN_EVENT = r'^-.\[.\].*$'
PATTERN_EVENT_TITLE_WITH_DATE = r'(?<=\])(.*?)(?=\`)'
PATTERN_EVENT_DATA = r'(?<=\`)(\d{2}.\d{2}.\d{4}?)(?=\`)'
PATTERN_EVENT_DATA_WITHOUT_DATE = r'^-.\[.\]((?!`).)*$'
PATTERN_EVENT_TITLE_FOR_BUY = r'(?<=\] Купить).*'


# todo деелать регулярки - добваить часы, минуты, продолжительность и возможность варьировать количесво цифр
def pars_dir_and_get_all_event(directory):
    calendar = []
    todo = []
    buying = []
    for file in os.listdir(directory):
        filename = f"{directory}/{file}"
        with open(filename) as f:
            calendar_projects = {'event_list': []}
            todo_projects = {'event_list': []}
            buying_projects = {'event_list': []}
            raw_data = f.read().splitlines()
            for line in raw_data:
                if line.strip():
                    for _ in re.finditer(PATTERN_PROJECT_NAME, line):
                        if 'project_name' in calendar_projects and len(calendar_projects['event_list']) != 0:
                            calendar.append(calendar_projects)
                            calendar_projects = {'event_list': [], 'project_name': line[3:].strip()}
                        else:
                            calendar_projects['project_name'] = line[3:].strip()
                        if 'project_name' in todo_projects and len(todo_projects['event_list']) != 0:
                            todo.append(todo_projects)
                            todo_projects = {'event_list': [], 'project_name': line[3:].strip()}
                        else:
                            todo_projects['project_name'] = line[3:].strip()
                        if 'project_name' in buying_projects and len(buying_projects['event_list']) != 0:
                            buying.append(buying_projects)
                            buying_projects = {'event_list': [], 'project_name': line[3:].strip()}
                        else:
                            buying_projects['project_name'] = line[3:].strip()
                    for _ in re.finditer(PATTERN_EVENT, line):
                        calendar_event = {}
                        for match in re.findall(PATTERN_EVENT_TITLE_WITH_DATE, line):
                            if line.find('~') == -1 and line.find('[x]') == -1 and line.find('`add`') == -1:
                                calendar_event['event_title'] = match
                                for match in re.findall(PATTERN_EVENT_DATA, line):
                                    calendar_event['event_data'] = match
                        if len(calendar_event) != 0:
                            calendar_projects['event_list'].append(calendar_event)
                        for match in re.finditer(PATTERN_EVENT_DATA_WITHOUT_DATE, line):
                            if line.find('~') == -1 and line.find('[x]') == -1 and line.find('Купить') == -1:
                                todo_projects['event_list'].append(match.string)
                        for match in re.finditer(PATTERN_EVENT_TITLE_FOR_BUY, line):
                            if line.find('~') == -1 and line.find('[x]') == -1:
                                buying_projects['event_list'].append(match.string)
            if len(calendar_projects['event_list']) != 0:
                calendar.append(calendar_projects)
            if len(todo_projects['event_list']) != 0:
                todo.append(todo_projects)
            if len(buying_projects['event_list']) != 0:
                buying.append(buying_projects)
        mark_add_event(filename, calendar)
    return calendar, todo, buying


def mark_done_event(delete_todo, pattern):
    done = []
    for file in os.listdir(delete_done_event.PROJECTS_DIR):  # todo можно выделить перебор в методе-генераторе
        change_condition = False
        filename = f"{delete_done_event.PROJECTS_DIR}/{file}"
        with open(filename, 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines):
                for matches in re.findall(pattern, line):
                    for match in matches:
                        if match.strip():
                            if any(match.strip() in s for s in delete_todo):
                                lines[i] = f"{line.split('[')[0]}[x]{line.split(']')[1]}"
                                change_condition = True
                                done.append(match.strip())
                                print(f"mark: {lines[i]}")
        if change_condition:
            with open(filename, 'w') as f:
                for line in lines:
                    f.write(line)

    return done


def add_in_calendar(projects: list, calendar_api: CalendarApi):
    if len(projects) != 0:
        calendar_events = calendar_api.get_calendar_events()
        for project in projects:
            for event in project['event_list']:
                date = event['event_data'].split('.')
                summary = f"{event['event_title']}({project['project_name']})"
                if not is_set_event(summary, calendar_events):
                    calendar_api.create_new_calendar_event(summary, project['project_name'],
                                                           y=int(date[2]),
                                                           m=int(date[1]),
                                                           d=int(date[0]))
                    print(f"add to calendar: {summary}")


def is_set_event(summary: str, events: list) -> bool:
    result = False
    for event in events:
        if event['summary'].find(summary.strip()) != -1:
            result = True
    return result


def add_in_file(event_list: list, file_path):
    with open(file_path, 'r') as f:
        todo_lines = f.readlines()
    with open(file_path, 'a') as f:
        for item in event_list:
            for event in item['event_list']:
                event = f"{event} ({item['project_name']})\n"
                if event not in todo_lines:
                    f.write(event)
                    print(f"add {file_path[-5:]}: {event.strip()}")


def get_mark_event(file_path):
    mark_event = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.find('~') != -1 or line.find('[x]') != -1:
                mark_event.append(line)

    return mark_event


def mark_add_event(file_path: str, calendar_events: list):
    if len(calendar_events) != 0:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        with open(file_path, 'w') as f:
            for line in lines:
                is_add = False
                for events in calendar_events:
                    for event in events['event_list']:
                        if line.find(event['event_title']) != -1:
                            line = line.rstrip() + ' `add`\n'
                            f.write(line)
                            is_add = True
                if not is_add:
                    f.write(line)


def get_all_add_events_in_file(directory):
    result = []
    for file in os.listdir(directory):
        file_path = f"{directory}/{file}"
        result.extend(get_add_event_in_file(file_path))

    return result


def get_add_event_in_file(file_path):
    result = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    for line in lines:
        if line.find('`add`') != -1:
            result.append(line)
    return result


def get_not_valid_calendar_events(calendar_api: CalendarApi):
    result = []
    file_events = get_all_add_events_in_file(delete_done_event.PROJECTS_DIR)
    calendar_events = calendar_api.get_calendar_events()
    for event in file_events:
        for match in re.findall(PATTERN_EVENT_TITLE_WITH_DATE, event):
            if not is_set_event(match, calendar_events):
                result.append(event)

    return result


if __name__ == '__main__':
    calendar_api = CalendarApi()
    mark_to_do = get_mark_event(BUYING_FILE_PATH)
    mark_buying = get_mark_event(TODO_FILE_PATH)
    mark_calendar = get_not_valid_calendar_events(calendar_api)
    mark_to_do.extend(mark_buying)
    mark_to_do.extend(mark_calendar)
    if len(mark_to_do) != 0:
        mark_done_event(mark_to_do, delete_done_event.PATTERN_EVENT_TITLE)
    calendar_events, todo, buying = pars_dir_and_get_all_event(delete_done_event.PROJECTS_DIR)
    add_in_file(todo, TODO_FILE_PATH)
    add_in_file(buying, BUYING_FILE_PATH)
    add_in_calendar(calendar_events, calendar_api)
