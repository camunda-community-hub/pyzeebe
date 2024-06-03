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


def with_job_parameter_and_param(x, job: Job):
    pass


def with_multiple_job_parameters(job: Job, job2: Job):
    pass


lambda_no_params = lambda: None
lambda_one_param = lambda x: None
lambda_multiple_params = lambda x, y, z: None
lambda_one_keyword_param = lambda x=0: None
lambda_multiple_keyword_params = lambda x=0, y=0, z=0: None
lambda_positional_and_keyword_params = lambda x, y=0: None
