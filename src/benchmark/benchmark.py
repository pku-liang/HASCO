from utils.logger import logger

from benchmark.computations import conv2d_compute, mm_compute, dwconv_compute, mttkrp_compute, ttm_compute
from codesign.config import supported_models
import re

class Workload:

    def __init__(self, name, tp, compute, args, stage=0): # stage is specific to mttkrp
        self.name = name
        self.type = tp
        self.compute = compute
        self.args = args
        arg_str = [str(i) for i in args]
        tag = '_'.join(arg_str)
        self.tag = name + "_" + tag
        self.stage = stage



class Benchmark:

    def __init__(self, name, workloads=None):
        self.name = name
        if workloads == None:
            workloads = []
        self.workloads = workloads 

    def add(self, workload):
        self.workloads.append(workload)



class BenchmarkCNN(Benchmark):

    def __init__(self, cnn, dtype, layout="GEMM"):

        if cnn in supported_models:
            from benchmark.keras_extend import get_model, get_workloads 

            input_size = "3,224,224"  # inpute image size to be customized
            INPUT_SIZE = tuple((int(d) for d in str.split(input_size, ",")))
            cnn_model = get_model(cnn, INPUT_SIZE[::-1])

            workloads = get_workloads(cnn_model, dtype, layout)
            
            super().__init__(cnn, workloads) 

        else:
            super().__init__(cnn)
            logger.error("Unimplemented benchmark!", exc_info = True)



