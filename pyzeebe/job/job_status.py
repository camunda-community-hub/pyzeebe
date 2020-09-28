from enum import Enum


class JobStatus(Enum):
    Running = "Running"
    Completed = "Completed"
    Failed = "Failed"
    ErrorThrown = "ErrorThrown"
