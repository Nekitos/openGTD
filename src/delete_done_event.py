#!/usr/bin/env python
import os
from google_calendar_api import CalendarApi
import re
import add_todo_and_calendar_event

PATTERN_EVENT_TITLE = r'(?<=\])(.*?)((?=\`)|(?=$))'
PROJECTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '3.Мне', 'Проекты'))
DONE_FILE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'Done.md'))


def delete_in_file(file_path):
    result = []
    with open(file_path, 'r') as f:
        lines = f.readlines()
    with open(file_path, 'w') as f:
        for line in lines:
            if line.find('~') == -1 and line.find('[x]') == -1:
                f.write(line)
            else:
                result.append(line)

    return result


def delete_done_event(directory):
    result = []
    for file in os.listdir(directory):
        file_path = f"{directory}/{file}"
        result.extend(delete_in_file(file_path))

    return result

def add_to_done(evens: list):
    with open(DONE_FILE_PATH, 'r') as f:
        lines = f.readlines()
    with open(DONE_FILE_PATH, 'a') as f:
        for event in evens:
            if event not in lines:
                f.write(event)
                print(f"add done: {event}")


# todo можно сделать и проверку на присутствие даты, чтобы лишний раз календарь не дергать
def delete_in_calendar(lines_list):
    if len(lines_list) != 0:
        calendar_api = CalendarApi()
        for line in lines_list:
            for matches in re.findall(PATTERN_EVENT_TITLE, line):
                for match in matches:
                    if match.strip():
                        calendar_api.delete_event(match)
                        print(f"del calendar: {match}")


if __name__ == '__main__':
    delete_buying = delete_in_file(add_todo_and_calendar_event.BUYING_FILE_PATH)
    delete_todo = delete_in_file(add_todo_and_calendar_event.TODO_FILE_PATH)
    delete_todo.extend(delete_buying)
    delete_projects = delete_done_event(PROJECTS_DIR)
    del_calendar = []
    for line in delete_projects:
        for _ in re.findall(add_todo_and_calendar_event.PATTERN_EVENT_TITLE_WITH_DATE, line):
            del_calendar.append(line)
    add_to_done(delete_todo)
    delete_in_calendar(del_calendar)
