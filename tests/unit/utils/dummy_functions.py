from pyzeebe.job.job import Job


def no_param():
    pass


def one_param(x):
    pass


def multiple_params(x, y, z):
    pass


def one_keyword_param(x=0):
    pass


def multiple_keyword_param(x=0, y=0, z=0):
    pass


def positional_and_keyword_params(x, y=0):
    pass


def args_param(*args):
    pass


def kwargs_param(**kwargs):
    pass


def standard_named_params(args, kwargs):
    pass


def with_job_parameter(job: Job):
    pass


def with_multiple_job_parameters(job: Job, job2: Job):
    pass


def lambda_no_params(): return None
def lambda_one_param(x): return None
def lambda_multiple_params(x, y, z): return None
def lambda_one_keyword_param(x=0): return None
def lambda_multiple_keyword_params(x=0, y=0, z=0): return None
def lambda_positional_and_keyword_params(x, y=0): return None
