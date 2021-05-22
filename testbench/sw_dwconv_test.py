import sys
sys.path.append("./src/")

from hw_generator.generator_conv import CONVGenerator 
from hw_generator.generator_gemm import GEMMGenerator 
from hw_generator.generator_gemv import GEMVGenerator
from hw_generator.generator_dot import DOTGenerator

from benchmark.benchmark import Workload, Benchmark
from codesign.hw_evaluation import evaluation_function_model, gen_software, reset

from benchmark.computations import dwconv_compute

if __name__ == '__main__':


    dtype = "int8"
    print("Testing accelerators with GEMM intrinsic ...")

    generator = GEMMGenerator() 
    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                        'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                        'dataflow': "OS", 'dtype':"int8"}
    benchmark = Benchmark("dwconv_test")
    dwconv1 = Workload("dwconv_1", "DWCONV", dwconv_compute, (1, 128, 32, 256, 1, 3, 3, 1, dtype, generator.type))  
    dwconv2 = Workload("dwconv_2", "DWCONV", dwconv_compute, (1, 64, 224, 224, 2, 3, 3, 1, dtype, generator.type))    
    benchmark.add(dwconv1)
    benchmark.add(dwconv2)
    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")
    print("Testing accelerators with CONV intrinsic ...")
    reset()
    generator = CONVGenerator() 
    parameterization = {'x':4, 'y':4, 'sp_capacity':2048, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}
    benchmark = Benchmark("dwconv_test")
    dwconv1 = Workload("dwconv_1", "DWCONV", dwconv_compute, (1, 128, 32, 256, 1, 3, 3, 1, dtype, generator.type))  
    dwconv2 = Workload("dwconv_2", "DWCONV", dwconv_compute, (1, 64, 224, 224, 2, 3, 3, 1, dtype, generator.type))  
    benchmark.add(dwconv1)
    benchmark.add(dwconv2)
    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")

  


