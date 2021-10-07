import sys
sys.path.append("./src/")
sys.path.append("./src/Ax/")

from hw_generator.generator_gemm import GEMMGenerator

from benchmark.benchmark import BenchmarkCNN
from codesign.hw_evaluation import gen_software
from codesign.explorer import codesign

stts = {
    "OS": [[1, 0, 0],
           [0, 1, 0],
           [1, 1, 1]],
    "WS": [[1, 0, 0],
           [0, 0, 1],
           [1, 1, 1]]
}


if __name__ == '__main__':
    dtype = "int8"
    method = "Model"
    hw_space = {
        "x": list(range(4, 33)),
        "y": list(range(4, 33)),
        "dma_buswidth": [64, 128, 256],
        "dataflow": list(stts.keys())
    }
    constraints = {"latency": 1000, "power": 20, "area": 0}  # TODO

    print("Testing accelerators with GEMM intrinsic ...")
    generator = GEMMGenerator(stts, hw_space, dtype)
    benchmark = BenchmarkCNN("MobileNetV2", dtype, layout=generator.type)
    codesign(benchmark, generator, method,
             constraints, init_size=10, trial_num=20)
    print("Passed.")
