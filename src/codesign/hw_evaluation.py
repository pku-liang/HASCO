import time, os

from codesign.ppa_model import MaestroModel, TENETModel, gen_config
# from codesign.manage_file import clean_file
from codesign.flextensor_extend import gen_schedules
from codesign.config import *

from utils.logger import logger
import tvm


PARAM_TABLE = {}

def evaluation_function(parameterization, benchmark, generator, method):
    if method == "Model":
        return evaluation_function_model(parameterization, benchmark, generator)
    else:
        logger.error("Unimplemented measure method yet.", exc_info = True)


def evaluation_function_model(parameterization, benchmark, generator):
    '''evaluating the holistic solution with models'''
    global PARAM_TABLE
    '''use tag and PARAM_TABLE to avoid reduandant evaluations'''
    arg_str = [str(i) for i in parameterization.values()] 
    tag = '_'.join(arg_str)

    if  tag in PARAM_TABLE:
        return PARAM_TABLE[tag][0]
    else:
        '''a new evaluation'''
        
        acc = generator.instantiate(parameterization, tag)  

        if acc.stt_matrix is None:
            config_file = gen_config(model_config_dir, parameterization, generator.type, tag)
            model = MaestroModel(maestro_path, config_file)
        else:
            model = TENETModel(tenet_path)

        if acc == None:
            PARAM_TABLE[tag] = None
            raise Exception("Invalid accelerator parameters.") 

        else:
            if verbose:
                acc.print_info()

            '''software evaluations for generating software and interface''' 
            schedules, all_tensors = gen_schedules(benchmark, acc, model)

            '''solution evaluations''' 
            mapping_file = mapping_dir + generator.type + "_" + benchmark.name +"_" + tag + ".m"
            l, t, p, _, a = model.evaluate(benchmark, schedules, acc, mapping_file)
            
            if l == model.max_val:
                PARAM_TABLE[tag] = None
                logger.error("Cannot find valid schedules.", exc_info = True) 

            rst =  {"latency": (l, 0.0), "throughput": (t, 0.0), "power": (p, 0.0), "area": (a, 0.0)} 
            
            PARAM_TABLE[tag] = (rst, list(zip(schedules, all_tensors)))

        '''clean up'''
        if verbose == False: 
             os.remove(rst_dir + config_file)
        return rst 


def gen_software(tag, is_print=False):
    global PARAM_TABLE
    st_list = PARAM_TABLE[tag][1]
    all_software = []
    for (schedule, tensors) in st_list:
        if not isinstance(schedule, tuple):
            schedule = (schedule, )
            tensors = (tensors, )
        for s, t in zip(schedule, tensors):
            try:
                software = tvm.lower(s, t, simple_mode=True)
                all_software.append(software)
                if is_print:
                    print(software)
            except Exception as e:
                continue
    return all_software

def reset():
    '''must reset for each benchmark or intrinsic, otherwise errors are expected'''
    from flextensor.intrinsic import reset_intrin
    global PARAM_TABLE
    PARAM_TABLE = {}
    reset_intrin()
