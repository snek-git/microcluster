# src/utilities.py
import json
import enum
from datetime import datetime

class JobState(enum.Enum):
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    FAILED = 4

class Job:
    def __init__(self, jobId, scriptPath, args=None, state=JobState.PENDING, submitTime=None, startTime=None, endTime=None):
        self.jobId = jobId
        self.scriptPath = scriptPath
        self.args = args or []
        self.state = state
        self.submitTime = submitTime or datetime.now()
        self.startTime = startTime
        self.endTime = endTime

    def to_dict(self):
        return {
            'jobId': self.jobId,
            'scriptPath': self.scriptPath,
            'args': self.args,
            'state': self.state.value,
            'submitTime': self.submitTime.isoformat(),
            'startTime': self.startTime.isoformat() if self.startTime else None,
            'endTime': self.endTime.isoformat() if self.endTime else None
        }

    @classmethod
    def from_dict(cls, data):
        data['state'] = JobState(data['state'])
        data['submitTime'] = datetime.fromisoformat(data['submitTime'])
        if data['startTime']:
            data['startTime'] = datetime.fromisoformat(data['startTime'])
        if data['endTime']:
            data['endTime'] = datetime.fromisoformat(data['endTime'])
        return cls(**data)

class JobResult:
    def __init__(self, jobId, success, output, error=None):
        self.jobId = jobId
        self.success = success
        self.output = output
        self.error = error

def serialize(obj):
    if isinstance(obj, enum.Enum):
        return obj.value
    if isinstance(obj, datetime):
        return obj.isoformat()
    if hasattr(obj, 'to_dict'):
        return json.dumps(obj.to_dict())
    if hasattr(obj, '__dict__'):
        return json.dumps({k: serialize(v) for k, v in obj.__dict__.items()})
    return json.dumps(str(obj))

def deserialize(jsonStr, cls):
    data = json.loads(jsonStr)
    if cls == Job:
        return Job.from_dict(data)
    return cls(**data)