import numpy as np
from ax import (
    ComparisonOp,
    ParameterType, 
    RangeParameter,
    ChoiceParameter,
    FixedParameter,
    SearchSpace, 
    Experiment, 
    OutcomeConstraint,
    OrderConstraint ,
    OptimizationConfig,
    Metric,
    Data
)
from ax.core.objective import MultiObjective, ScalarizedObjective
from ax.metrics.l2norm import L2NormMetric
from ax.modelbridge.registry import Models
from ax.plot.contour import plot_contour
from ax.plot.trace import optimization_trace_single_method
from ax.utils.measurement.synthetic_functions import hartmann6
from ax.utils.notebook.plotting import render, init_notebook_plotting
from ax.runners.synthetic import SyntheticRunner
from ax.service.utils.best_point import (
    get_best_parameters,
    get_best_raw_objective_point
)
from ax.modelbridge.factory import get_botorch, get_MOO_EHVI


from codesign.ax_extend import eval_exp, run_trial, get_non_dominated, get_size
from codesign.config import intrinsic_lib, eval_methods, all_metrics, verbose, sw_dir
from codesign.hw_evaluation import evaluation_function, gen_software

from typing import Optional, Any

from utils.logger import logger
 


INIT_SIZE = 10
TRIAL_NUM = 20
EARLY_STOP = 5
ABANDON_LIMITS = 20   



def build_hw_space(generator, constraints, method):
    """ Create hardware parameter search space. 

        Parameters
        ----------
        generator : generator
            Generator info.
        constraints : dict
            constraint dictionary.
        method : str
            Measure method.
        Returns
        -------
        Experiment
            The experiment to be evaluated.

        """ 

    '''
    memory capacity unit: KiB
    buswidth unit: bits
    '''

    if generator.type == "GEMM":
        hw_design_space = SearchSpace(parameters=[
            ChoiceParameter(name="x", parameter_type=ParameterType.INT, values=[8, 16, 32]),   
            ChoiceParameter(name="sp_capacity", parameter_type=ParameterType.INT, values=[128, 256, 512]), 
            ChoiceParameter(name="local_capacity", parameter_type=ParameterType.INT, values=[64, 128, 256]), 
            ChoiceParameter(name="dataflow", parameter_type=ParameterType.STRING, values=["WS", "OS"]), 
            RangeParameter(name="sp_banks", parameter_type=ParameterType.INT, lower=1, upper=8),
            ChoiceParameter(name="dma_buswidth", parameter_type=ParameterType.INT, values=[64, 128]), 
            ChoiceParameter(name="dma_maxbytes", parameter_type=ParameterType.INT, values=[64, 128]),
            FixedParameter(name="dtype", parameter_type=ParameterType.STRING, value=generator.dtype), 
        ])  # can be improved by constraining local_capacity < sp_capacity

    elif generator.type == "GEMV":
        hw_design_space = SearchSpace(parameters=[
            ChoiceParameter(name="x", parameter_type=ParameterType.INT, values=[8, 16, 32]), 
            ChoiceParameter(name="sp_capacity", parameter_type=ParameterType.INT, values=[128, 256, 512]), 
            ChoiceParameter(name="local_capacity", parameter_type=ParameterType.INT, values=[64, 128, 256]), 
            FixedParameter(name="dataflow", parameter_type=ParameterType.STRING, value="FIXED"), 
            RangeParameter(name="sp_banks", parameter_type=ParameterType.INT, lower=1, upper=8),
            ChoiceParameter(name="dma_buswidth", parameter_type=ParameterType.INT, values=[64, 128]), 
            ChoiceParameter(name="dma_maxbytes", parameter_type=ParameterType.INT, values=[64, 128]),
            FixedParameter(name="dtype", parameter_type=ParameterType.STRING, value=generator.dtype), 
        ]) 
    else: # conv  dot 
       hw_design_space = SearchSpace(parameters=[
            RangeParameter(name="x", parameter_type=ParameterType.INT, lower=4, upper=32),
            RangeParameter(name="y", parameter_type=ParameterType.INT, lower=4, upper=32),
            ChoiceParameter(name="sp_capacity", parameter_type=ParameterType.INT, values=[128, 256, 512, 1024]), 
            ChoiceParameter(name="local_capacity", parameter_type=ParameterType.INT, values=[64, 128, 256, 512]), 
            RangeParameter(name="sp_banks", parameter_type=ParameterType.INT, lower=1, upper=8),
            ChoiceParameter(name="dma_buswidth", parameter_type=ParameterType.INT, values=[64, 128, 256]), 
            ChoiceParameter(name="dma_maxbytes", parameter_type=ParameterType.INT, values=[64, 128, 256]),
            FixedParameter(name="dataflow", parameter_type=ParameterType.STRING, value="FIXED"), 
            FixedParameter(name="dtype", parameter_type=ParameterType.STRING, value=generator.dtype), 
        ])

    metrics = []
    for key in constraints:
        if key != "throughput":
            metrics.append(Metric(name=key, lower_is_better=True))
        else:
            metrics.append(Metric(name=key, lower_is_better=False))

    #create experiment
    optimization_config = OptimizationConfig(
        objective=ScalarizedObjective( metrics=metrics, minimize=True)
    )


    exp = Experiment(
        name="codesign_process",
        search_space=hw_design_space,
        runner=SyntheticRunner(),
        optimization_config=optimization_config
    ) 

    return exp




def codesign(benchmark, generator, method, constraints, init_size=INIT_SIZE, trial_num=TRIAL_NUM, early_stop=EARLY_STOP):

    print("#"*50)
    assert generator.type in intrinsic_lib, "unsupported generator"
    assert method in eval_methods, "measure method to be updated"
    print("Generator Intrinsic: " + generator.type)
    print("Evaluation Method: " + method)
    print("Constraints: ", end='')
    for key in constraints:
        assert key in all_metrics, "unsupported metric"
        print(key + "  ", end='')

    print("\nStarting ..." + "."*30)

    '''buidling hardware design space'''
    exp =  build_hw_space(generator, constraints, method)

    pareto_results = {}
    tags = {}
    for key in constraints:
        pareto_results[key] = [] 
        tags[key] = [] 


    '''starting MOBO-based exploration'''
    '''MOBO: init the prior'''
    sobol = Models.SOBOL(exp.search_space)
    data= None
    while data == None:
        print("Running Sobol initialization trials...")
        exp.new_batch_trial(generator_run=sobol.gen(init_size))
        data=eval_exp(exp, evaluation_function, benchmark=benchmark, generator=generator, method=method)
    
    data_size = get_size(data)
    same_cnt = 0
    '''MOBO: iterative update'''
    for i in range(trial_num):
        print(f"Running GP+EHVI optimization trial {i+1}/{trial_num}...")

        '''Reinitialize GP+EHVI model at each step with updated data'''
        moo_model = get_MOO_EHVI(
            experiment=exp,
            data=data,
            ref_point=constraints,
            search_space=exp.search_space
        )
    
        for index in range(ABANDON_LIMITS): 
            trial = exp.new_trial(generator_run=moo_model.gen(1)) # can be improved
            try:
                new_data = run_trial(exp, trial, evaluation_function, benchmark=benchmark, generator=generator, method=method)
                data = Data.from_multiple_data([data, new_data])
                break
            except Exception:
                # print("Abandon this trail and start a new one...")
                trial.mark_abandoned()
                continue

        
        current_pareto = get_non_dominated(exp) 
        for items in current_pareto:
            for (k, v) in items.items():
                tags[k].append(v[0])
                pareto_results[k].append(v[1])


        
        if get_size(data) == data_size:
            same_cnt += 1
            if same_cnt >= early_stop:
                print(f"Early quit at the #{i+1} trial ...")
                break
        else:
            same_cnt = 0

        data_size = get_size(data)


    print("#"*50 + "\nReport:", end='')
    print(pareto_results)
    print(tags)
    print("#"*50 +"\nSaving Results ...")


    '''saving software'''
    import json
    for key in constraints:
        tag = tags[key][-1] 
        acc_software = gen_software(tag) 
        params = tag.split('_')
        acc = generator.instantiate(params, tag)
        jsonString = json.dumps(str(acc_software))
        jsonFile = open("{}{}_{}_{}_software.json".format(sw_dir, benchmark.name, acc.name, key), "w")
        jsonFile.write(jsonString)
        jsonFile.close()
        print(f"{key} done!")

    print("All Done!")


    
 
