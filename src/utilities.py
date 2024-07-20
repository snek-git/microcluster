# src/utilities.py
import json
import enum
from datetime import datetime

class JobState(enum.Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4
    CANCELLED = 5

class Job:
    def __init__(self, jobId, userId, scriptPath, args=None):
        self.jobId = jobId
        self.userId = userId
        self.scriptPath = scriptPath
        self.args = args or []
        self.state = JobState.PENDING
        self.submitTime = datetime.now()
        self.startTime = None
        self.endTime = None

    def to_dict(self):
        return {
            'jobId': self.jobId,
            'userId': self.userId,
            'scriptPath': self.scriptPath,
            'args': self.args,
            'state': self.state.value,
            'submitTime': self.submitTime.isoformat(),
            'startTime': self.startTime.isoformat() if self.startTime else None,
            'endTime': self.endTime.isoformat() if self.endTime else None
        }

class JobResult:
    def __init__(self, jobId, success, output, error=None):
        self.jobId = jobId
        self.success = success
        self.output = output
        self.error = error

def serialize(obj):
    if isinstance(obj, enum.Enum):
        return json.dumps(obj.value)
    if isinstance(obj, datetime):
        return json.dumps(obj.isoformat())
    if hasattr(obj, 'to_dict'):
        return json.dumps(obj.to_dict())
    if hasattr(obj, '__dict__'):
        return json.dumps({k: serialize(v) for k, v in obj.__dict__.items()})
    return json.dumps(str(obj))

def deserialize(jsonStr, cls):
    data = json.loads(jsonStr)
    if cls == Job:
        data['state'] = JobState(data['state'])
        data['submitTime'] = datetime.fromisoformat(data['submitTime'])
        if data['startTime']:
            data['startTime'] = datetime.fromisoformat(data['startTime'])
        if data['endTime']:
            data['endTime'] = datetime.fromisoformat(data['endTime'])
    return cls(**data)