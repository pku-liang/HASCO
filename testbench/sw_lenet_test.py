import sys
sys.path.append("./src/")

from hw_generator.generator_conv import CONVGenerator 
from hw_generator.generator_gemm import GEMMGenerator

from benchmark.benchmark import Workload, Benchmark
from codesign.hw_evaluation import evaluation_function_model, gen_software, reset

from benchmark.computations import conv2d_compute, mm_compute

if __name__ == '__main__':


    dtype = "int8"
    print("Testing accelerators with CONV intrinsic ...")
    generator = CONVGenerator() 
    parameterization = {'x':4, 'y':4, 'sp_capacity':2048, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}
    benchmark = Benchmark("LeNet")
    conv1 = Workload("conv_1", "CONV", conv2d_compute, (1, 1, 32, 32, 6, 5, 5, 1, dtype, generator.type, False))  
    conv2 = Workload("conv_2", "CONV", conv2d_compute, (1, 6, 14, 14, 16, 5, 5, 1, dtype, generator.type, False))  
    conv3 = Workload("conv_3", "CONV", conv2d_compute, (1, 16, 5, 5, 120, 5, 5, 1, dtype, generator.type, False))  
    mm1 = Workload("fc_1", "GEMM", mm_compute, (1, 84, 120, dtype, generator.type)) 
    mm2 = Workload("fc_2", "GEMM", mm_compute, (1, 10, 84, dtype, generator.type))  
    benchmark.add(conv1) 
    benchmark.add(conv2) 
    benchmark.add(conv3) 
    benchmark.add(mm1) 
    benchmark.add(mm2) 

    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")


    print("Testing accelerators with GEMM intrinsic ...")
    reset()
    generator = GEMMGenerator() 
    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                        'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                        'dataflow': "OS", 'dtype':"int8"}

    benchmark = Benchmark("LeNet")
    conv1 = Workload("conv_1", "CONV", conv2d_compute, (1, 1, 32, 32, 6, 5, 5, 1, dtype, generator.type, False))  
    conv2 = Workload("conv_2", "CONV", conv2d_compute, (1, 6, 14, 14, 16, 5, 5, 1, dtype, generator.type, False))  
    conv3 = Workload("conv_3", "CONV", conv2d_compute, (1, 16, 5, 5, 120, 5, 5, 1, dtype, generator.type, False))  
    mm1 = Workload("fc_1", "GEMM", mm_compute, (1, 84, 120, dtype, generator.type)) 
    mm2 = Workload("fc_2", "GEMM", mm_compute, (1, 10, 84, dtype, generator.type))  
    benchmark.add(conv1) 
    benchmark.add(conv2) 
    benchmark.add(conv3) 
    benchmark.add(mm1) 
    benchmark.add(mm2) 

    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")
  


