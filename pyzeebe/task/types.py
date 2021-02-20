from typing import Callable

from pyzeebe import Job

DecoratorRunner = Callable[[Job], Job]
JobHandler = Callable[[Job], Job]
