import sys
sys.path.append("./src/")

from hw_generator.generator_gemm import GEMMGenerator
from hw_generator.generator_conv import CONVGenerator
from hw_generator.generator_gemv import GEMVGenerator
from hw_generator.generator_dot import DOTGenerator

from benchmark.benchmark import Workload, Benchmark
from codesign.hw_evaluation import evaluation_function_model, gen_software, reset

from benchmark.computations import mm_compute

if __name__ == '__main__':


    dtype = "int8"

    print("Testing accelerators with GEMM intrinsic ...")

    generator = GEMMGenerator() 

    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                        'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                        'dataflow': "OS", 'dtype':"int8"}

    benchmark = Benchmark("mm_test")

    mm1 = Workload("mm_1", "GEMM", mm_compute, (256, 512, 1024, dtype, generator.type)) 
    mm2 = Workload("mm_2", "GEMM", mm_compute, (64, 64, 64, dtype, generator.type)) 
    benchmark.add(mm1)
    benchmark.add(mm2)

    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")
    print("Testing accelerators with CONV intrinsic ...")  # We treat GEMMs as 1x1 CONVs
    reset()
    generator = CONVGenerator() 
    parameterization = {'x':4, 'y':4, 'sp_capacity':2048, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}
    benchmark = Benchmark("mm_test")
    mm1 = Workload("mm_1", "GEMM", mm_compute, (256, 512, 1024, dtype, generator.type)) 
    mm2 = Workload("mm_2", "GEMM", mm_compute, (256, 64, 1024, dtype, generator.type))  #64 64 64 64
    benchmark.add(mm1)
    benchmark.add(mm2)

    evaluation_function_model(parameterization, benchmark, generator)

    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    
    print("Passed.")
    print("Testing accelerators with GEMV intrinsic ...")
    reset()
    generator = GEMVGenerator() 
    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}
    benchmark = Benchmark("mm_test")
    mm1 = Workload("mm_1", "GEMM", mm_compute, (256, 512, 1024, dtype, generator.type)) 
    mm2 = Workload("mm_2", "GEMM", mm_compute, (256, 64, 1024, dtype, generator.type))  #64 64 64 64
    benchmark.add(mm1)
    benchmark.add(mm2)

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
    benchmark = Benchmark("mm_test")
    mm1 = Workload("mm_1", "GEMM", mm_compute, (256, 512, 1024, dtype, generator.type)) 
    mm2 = Workload("mm_2", "GEMM", mm_compute, (64, 64, 64, dtype, generator.type)) 
    benchmark.add(mm1)
    benchmark.add(mm2) 
    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")



