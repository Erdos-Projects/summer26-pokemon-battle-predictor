import time, os
from threading import Thread, current_thread
from multiprocessing import Process, current_process,Pool
from concurrent.futures import ThreadPoolExecutor


COUNT = 200000000

def cpu_bound(n):

    pid = os.getpid()
    threadName = current_thread().name
    processName = current_process().name

    print(f"{pid} * {processName} * {threadName} \
        ---> Start counting...")

    while n>0:
        n -= 1

    print(f"{pid} * {processName} * {threadName} \
        ---> Finished counting...")

if __name__=="__main__":
    start = time.time()

    with ThreadPoolExecutor() as executor:
        executor.submit(cpu_bound,COUNT)

    end = time.time()
    print('Multithreading time taken in seconds -', end - start)

    start = time.time()
    with Pool(1) as pool:
        pool.apply(cpu_bound,args=(COUNT,))
        pool.apply(cpu_bound,args=(COUNT,))
    end = time.time()
    print('Synchronous multiprocessing (1 process) time taken in seconds -', end-start)

    start = time.time()
    with Pool(2) as pool:
        pool.apply(cpu_bound,args=(COUNT,))
        pool.apply(cpu_bound,args=(COUNT,))
    end = time.time()
    print('Synchronous multiprocessing (2 processes) time taken in seconds -', end-start)

    start = time.time()
    with Pool(1) as pool:
        result = pool.apply_async(cpu_bound,args=(COUNT,))
        result.get()
    end = time.time()
    print('Asynchronous multiprocessing (1 process) time taken in seconds -', end-start)

    start = time.time()
    with Pool(2) as pool:
        result = pool.apply_async(cpu_bound,args=(COUNT,))
        result.get()
    end = time.time()
    print('Asynchronous multiprocessing (2 processes) time taken in seconds -', end-start)