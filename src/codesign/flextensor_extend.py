import time
import os

from flextensor.task import Task
from flextensor.micro_scheduler import gen_micro_schedule
from flextensor.utils import get_iter_info

from codesign.config import mapping_dir
from utils.logger import logger
from benchmark.benchmark import Benchmark, Workload
from benchmark.computations import ttm_compute, gemv_compute


from tqdm import tqdm


def gen_schedules(benchmark, accelerator, model):

    '''generate schedules for each workload. a schedule indicates the tensorize choice and sotware optimization'''

   
    '''use WORKLOAD_TABLE to avoid reduandant workloads'''
    WORKLOAD_TABLE = {}
    schedules = []
    all_tensors = []
    for i in tqdm(range(len(benchmark.workloads))):
        workload = benchmark.workloads[i]
        st_tuple = WORKLOAD_TABLE.get(workload.tag) 
        if st_tuple != None:
            '''skip exploration'''
            schedules.append(st_tuple[0])
            all_tensors.append(st_tuple[1])
            continue

        name = workload.name
        compute = workload.compute
        args = workload.args  

        def sw_eval(workload, task, accelerator):
            '''software evaluation'''
            tmp_benchmark = Benchmark(workload.name, [workload])
            def model_func(schedule):
                t = time.time()
                pid = os.getpid()

                mapping_file = "{}{}_{}_{}_{}.m".format(mapping_dir, accelerator.type, tmp_benchmark.name, str(int(round(t*1000000))), str(pid))
                l, t , p, e, a = model.evaluate(tmp_benchmark, schedule, accelerator, mapping_file)
                return l

            return gen_micro_schedule(task, accelerator.target, model_func)

    
        if workload.type == "MTTKRP":
            workload.stage = 1 
            task1 = Task(name, accelerator.name + name + "_stage1", compute, args + (1,), "micro", 0) 
            schedule1, tensors1 = sw_eval(workload, task1, accelerator)
            # print(schedule1)
            workload.stage = 2
            task2 = Task(name, accelerator.name + name + "_stage2", compute, args + (2,), "micro", 0)
            schedule2, tensors2 = sw_eval(workload, task2, accelerator)
            # print(schedule2)
            schedule = (schedule1, schedule2)
            tensors = (tensors1, tensors2)
            workload.stage = 0
        else:
            task = Task(name, accelerator.name + name, compute, args, "micro", 0)
            schedule, tensors = sw_eval(workload, task, accelerator)   # TODO
            if schedule == None:
                return None, None
            # print(schedule)
        WORKLOAD_TABLE[workload.tag] = (schedule, tensors) 
        schedules.append(schedule)
        all_tensors.append(tensors)

    return schedules, all_tensors  


def parse_schedule(schedule):
    if isinstance(schedule, dict):
        loop_info = schedule
    else: 
        loop_info = get_iter_info(schedule)

    return loop_info