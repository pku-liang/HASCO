import sys
sys.path.append("./src/")

from hw_generator.generator_gemm import GEMMGenerator
from hw_generator.generator_gemv import GEMVGenerator
from hw_generator.generator_dot import DOTGenerator

from benchmark.benchmark import Workload, Benchmark
from codesign.hw_evaluation import evaluation_function_model, gen_software, reset

from benchmark.computations import ttm_compute

if __name__ == '__main__':


    dtype = "int8"

    print("Testing accelerators with GEMM intrinsic ...")

    generator = GEMMGenerator() 

    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                        'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                        'dataflow': "OS", 'dtype':"int8"}

    benchmark = Benchmark("ttm_test")

    ttm1 = Workload("ttm_1", "TTM", ttm_compute, (128, 256, 512, 1024, dtype, generator.type)) 
    ttm2 = Workload("ttm_2", "TTM", ttm_compute, (64, 64, 64, 64, dtype, generator.type)) 
    benchmark.add(ttm1)
    benchmark.add(ttm2)

    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")

    ''' matching the CONV intrinsic will lead to an error, which is expected.  '''
    
    print("Testing accelerators with GEMV intrinsic ...")
    reset()
    generator = GEMVGenerator() 
    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}
    benchmark = Benchmark("ttm_test")
    ttm1 = Workload("ttm_1", "TTM", ttm_compute, (128, 256, 512, 1024, dtype, generator.type)) 
    ttm2 = Workload("ttm_2", "TTM", ttm_compute, (64, 256, 64, 1024, dtype, generator.type))  #64 64 64 64
    benchmark.add(ttm1)
    benchmark.add(ttm2)

    evaluation_function_model(parameterization, benchmark, generator)

    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    
    print("Passed.")
    print("Testing accelerators with DOT intrinsic ...")
    reset()
    generator = DOTGenerator() 
    parameterization = {'x':16, 'y':8, 'sp_capacity':512, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}     
    benchmark = Benchmark("ttm_test")
    ttm1 = Workload("ttm_1", "TTM", ttm_compute, (128, 256, 512, 1024, dtype, generator.type)) 
    ttm2 = Workload("ttm_2", "TTM", ttm_compute, (64, 64, 64, 64, dtype, generator.type)) 
    benchmark.add(ttm1)
    benchmark.add(ttm2) 
    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")



