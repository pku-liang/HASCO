import sys
sys.path.append("./src/")
sys.path.append("./src/Ax/")

from hw_generator.generator_gemm import GEMMGenerator

from benchmark.benchmark import BenchmarkCNN
from codesign.hw_evaluation import gen_software
from codesign.explorer import codesign



if __name__ == '__main__':
    dtype = "int8"
    method = "Model"
    constraints = {"latency": 0, "power": 0, "area": 0}  # TODO

    print("Testing accelerators with GEMM intrinsic ...")
    generator = GEMMGenerator() 
    benchmark = BenchmarkCNN("MobileNetV2", dtype, layout=generator.type) 
    codesign(benchmark, generator, method, constraints, init_size=5, trial_num=20)
    print("Passed.")
