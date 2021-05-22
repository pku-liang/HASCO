import sys
sys.path.append("./src/")

from hw_generator.generator_gemv import GEMVGenerator 

from benchmark.benchmark import Workload, Benchmark
from codesign.hw_evaluation import evaluation_function_model, gen_software

from benchmark.computations import gemv_compute

if __name__ == '__main__':


    dtype = "int8"
    print("Testing accelerators with GEMV intrinsic ...")

    generator = GEMVGenerator() 
    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}
    benchmark = Benchmark("gemv_test")
    gemv = Workload("gemv_1", "GEMV", gemv_compute, (128, 256, 512, dtype, generator.type))  
    benchmark.add(gemv) 
    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")
  


