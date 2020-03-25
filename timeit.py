from functools import wraps
import time


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        print('Execution time of {}(): {}s'.format(
            func.__qualname__, round(time.time() - start, 5)))
        return result
    return wrapper
