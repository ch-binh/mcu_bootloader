import time

def measure_exe_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"[DBG] {func.__name__} executed in {end - start:.6f} seconds")
        return result
    return wrapper