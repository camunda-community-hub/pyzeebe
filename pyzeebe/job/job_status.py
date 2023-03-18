from enum import Enum


class JobStatus(Enum):
    Running = "Running"
    Completed = "Completed"
    RunningAfterDecorators = "RunningAfterDecorators"
    Failed = "Failed"
    ErrorThrown = "ErrorThrown"
