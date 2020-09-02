from enum import Enum


class TaskStatus(Enum):
    Running = 'Running'
    Completed = 'Completed'
    Failed = 'Failed'
    ErrorThrown = 'ErrorThrown'
