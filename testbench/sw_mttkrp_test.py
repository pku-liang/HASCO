import sys
sys.path.append("./src/")

from hw_generator.generator_gemv import GEMVGenerator
from hw_generator.generator_dot import DOTGenerator

from benchmark.benchmark import Workload, Benchmark
from codesign.hw_evaluation import evaluation_function_model, gen_software, reset

from benchmark.computations import mttkrp_compute

if __name__ == '__main__':


    dtype = "int8"

 
    """
    matching the CONV intrinsic will lead to an error, which is expected.
    GEMM cannot match all stages. 
    """


    print("Testing accelerators with GEMV intrinsic ...")
    generator = GEMVGenerator() 
    parameterization = {'x':16, 'sp_capacity':512, 'local_capacity':1024, 
                            'sp_banks':4, 'dma_buswidth':256, 'dma_maxbytes':128, 
                            'dataflow': "FIXED", 'dtype':"int8"}
    benchmark = Benchmark("mttkrp_test")
    mttkrp1 = Workload("mttkrp_1", "MTTKRP", mttkrp_compute, (128, 256, 512, 1024, dtype, generator.type)) 
    mttkrp2 = Workload("mttkrp_2", "MTTKRP", mttkrp_compute, (64, 64, 64, 64, dtype, generator.type)) 
    benchmark.add(mttkrp1)
    benchmark.add(mttkrp2)

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
    benchmark = Benchmark("mttkrp_test")
    mttkrp1 = Workload("mttkrp_1", "MTTKRP", mttkrp_compute, (128, 256, 512, 1024, dtype, generator.type)) 
    mttkrp2 = Workload("mttkrp_2", "MTTKRP", mttkrp_compute, (64, 64, 64, 64, dtype, generator.type)) 
    benchmark.add(mttkrp1)
    benchmark.add(mttkrp2)
    evaluation_function_model(parameterization, benchmark, generator)
    arg_str = [str(i) for i in parameterization.values()]
    tag = '_'.join(arg_str)
    software = gen_software(tag, is_print=True)
    print("Passed.")



