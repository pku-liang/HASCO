import sys
sys.path.append("./src/")
sys.path.append("./src/Ax/")

from hw_generator.generator_conv import CONVGenerator

from benchmark.benchmark import BenchmarkCNN
from codesign.hw_evaluation import gen_software
from codesign.explorer import codesign

if __name__ == '__main__':
    dtype = "int8"
    method = "Model"
    stts = {
        "WS": [[1, 0, 0, 0, 0, 0],
               [0, 1, 0, 0, 0, 0],
               [1, 1, 0, 1, 0, 0],
               [0, 0, 0, 0, 0, 1],
               [0, 0, 0, 0, 1, 0],
               [0, 0, 1, 0, 0, 0]],
        "NVDLA": [[1, 0, 0, 0, 0, 0],
                  [0, 1, 0, 0, 0, 0],
                  [0, 0, 1, 0, 0, 0],
                  [0, 0, 0, 1, 0, 0],
                  [0, 0, 0, 0, 1, 0],
                  [0, 0, 0, 0, 0, 1]]
    }   
    hw_space = {
        "x":[4,8,16,32],
        "y":[4,8,16,32],
        "dma_buswidth":[64,128,256],
        "dataflow":list(stts.keys())
    }
    constraints = {"latency": 1000, "power": 20, "area": 0}  # TODO

    print("Testing accelerators with CONV intrinsic ...")
    generator = CONVGenerator(stts, hw_space, dtype)
    benchmark = BenchmarkCNN("MobileNetV2", dtype, layout=generator.type)
    codesign(benchmark, generator, method,
             constraints, init_size=10, trial_num=20)
    print("Passed.")
