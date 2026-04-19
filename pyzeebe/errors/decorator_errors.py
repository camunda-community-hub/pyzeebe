class NonRecoverableDecoratorError(Exception):
    "Raised when a decorator encounters a critical error and the job should fail."
    pass
