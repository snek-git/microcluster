# common.py
import json
import enum


class TaskType(enum.Enum):
    SHELL_SCRIPT = 1
    PYTHON_FUNCTION = 2
    EXECUTABLE = 3


class Task:
    def __init__(self, task_id, user_id, task_type, content, args=None):
        self.task_id = task_id
        self.user_id = user_id
        self.task_type = task_type
        self.content = content
        self.args = args or []


class Result:
    def __init__(self, task_id, success, output, error=None):
        self.task_id = task_id
        self.success = success
        self.output = output
        self.error = error


def serialize(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    return json.dumps(obj, default=lambda o: o.__dict__)


def deserialize(json_str, cls):
    data = json.loads(json_str)
    if cls == Task:
        data['task_type'] = TaskType(data['task_type'])
    return cls(**data)