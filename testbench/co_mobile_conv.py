import sys
sys.path.append("./src/")
sys.path.append("./src/Ax/")

from hw_generator.generator_conv import CONVGenerator

from benchmark.benchmark import BenchmarkCNN
from codesign.hw_evaluation import gen_software
from codesign.explorer import codesign

stt = [[1, 0, 0, 0, 0, 0],
       [0, 1, 0, 0, 0, 0],
       [1, 1, 0, 1, 0, 0],
       [0, 0, 0, 0, 0, 1],
       [0, 0, 0, 0, 1, 0],
       [0, 0, 1, 0, 0, 0]]

if __name__ == '__main__':
    dtype = "int8"
    method = "Model"
    constraints = {"latency": 0, "power": 0, "area": 0}  # TODO

    print("Testing accelerators with CONV intrinsic ...")
    generator = CONVGenerator(stt) 
    benchmark = BenchmarkCNN("MobileNetV2", dtype, layout=generator.type) 
    codesign(benchmark, generator, method, constraints, init_size=10, trial_num=40)
    print("Passed.")
