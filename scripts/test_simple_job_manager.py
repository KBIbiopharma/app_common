from time import sleep, time
from logging import getLogger, DEBUG, StreamHandler
from app_common.encore.simple_async_job_manager import SimpleAsyncJobManager

logger = getLogger()
logger.setLevel(DEBUG)
hdlr = StreamHandler()
hdlr.level = DEBUG
logger.addHandler(hdlr=hdlr)


def sleeper(sleep_time):
    """ Function to execute in parallel.
    """
    sleep(sleep_time)
    return {"sleep_time": sleep_time}


jm = SimpleAsyncJobManager()


# Version 1: async_map type interface

t0 = time()
jm.async_map(sleeper, [2]*5)
duration = time()-t0
print("All jobs submitted in {} seconds".format(duration))
jm.wait()
duration = time()-t0
print("All jobs run in {} seconds".format(duration))


# Version 2: flexible generator type interface

def job_generator(num_jobs, sleep_time=3):
    """ Generator yielding work items belonging to the same job.
    """
    for i in range(num_jobs):
        yield sleeper, (sleep_time,), {}

t0 = time()
jm.submit(job_generator, 5, sleep_time=2)
duration = time()-t0
print("All jobs submitted in {} seconds".format(duration))
jm.wait()
duration = time()-t0
print("All jobs run in {} seconds".format(duration))
