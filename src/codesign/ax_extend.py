import inspect
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from ax.core.arm import Arm
from ax.core.base_trial import BaseTrial, TrialStatus
from ax.core.batch_trial import BatchTrial
from ax.core.data import Data
from ax.core.experiment import Experiment
from ax.core.metric import Metric
from ax.core.objective import Objective
from ax.core.optimization_config import OptimizationConfig
from ax.core.outcome_constraint import OutcomeConstraint
from ax.core.search_space import SearchSpace
from ax.core.trial import Trial
from ax.core.types import TEvaluationOutcome, TParameterization, TTrialEvaluation
from ax.utils.common.docutils import copy_doc
from ax.utils.common.typeutils import not_none, numpy_type_to_python_type, checked_cast


from ax.utils.notebook.plotting import render
from ax.plot.trace import optimization_trace_single_method
from ax.plot.helper import _format_dict


def eval_trial(exp, trial, func, kwargs):
    """
    Evaluate trial arms with the evaluation function of this
    experiment.

    kwargs:
        trial: trial, whose arms to evaluate.
    """
    cached_data = exp.lookup_data_for_trial(trial.index)[0]
    if not cached_data.df.empty:
        return cached_data

    evaluations = {}
    trial.runner = exp.runner
    if isinstance(trial, Trial):
        if not trial.arm:
            return Data()  # pragma: no cover
        trial.mark_running()
        evaluations[not_none(trial.arm).name] = evaluation_function_outer(exp, func,
                                                                          not_none(
                                                                              trial.arm).parameters, kwargs, None
                                                                          )
    elif isinstance(trial, BatchTrial):
        if not trial.arms:
            return Data()  # pragma: no cover
        trial.mark_running()
        for arm, weight in trial.normalized_arm_weights().items():
            arm_parameters: TParameterization = arm.parameters
            try:
                evaluations[arm.name] = evaluation_function_outer(exp, func,
                                                                  arm_parameters, kwargs, weight)
            except Exception as e:
                print(e)
                continue

    trial.mark_completed()
    try:
        data = Data.from_evaluations(evaluations, trial.index)
        exp.attach_data(data)
        return data
    except ValueError as e:
        print(e)
        return Data()


def evaluation_function_outer(
    exp, func, parameterization: TParameterization, kwargs, weight: Optional[float] = None
) -> TTrialEvaluation:
    signature = inspect.signature(func)
    num_evaluation_function_params = len(
        signature.parameters.items()) - len(kwargs)
    if num_evaluation_function_params == 1:
        # pyre-fixme[20]: Anonymous call expects argument `$1`.
        evaluation = func(
            parameterization, kwargs['benchmark'], kwargs['generator'], kwargs['method'])
    elif num_evaluation_function_params == 2:
        evaluation = func(parameterization, weight,
                          kwargs['benchmark'], kwargs['generator'], kwargs['method'])
    else:
        raise ValueError(  # pragma: no cover
            "Evaluation function must take either one parameter "
            "(parameterization) or two parameters (parameterization and weight)."
        )

    if isinstance(evaluation, dict):
        return evaluation
    elif isinstance(evaluation, tuple):
        return {exp.optimization_config.objective.metric.name: evaluation}
    elif isinstance(evaluation, (float, int)):
        return {exp.optimization_config.objective.metric.name: (evaluation, 0.0)}
    elif isinstance(evaluation, (np.float32, np.float64, np.int32, np.int64)):
        return {
            exp.optimization_config.objective.metric.name: (
                numpy_type_to_python_type(evaluation),
                0.0,
            )
        }
    raise Exception(  # pragma: no cover
        "Evaluation function returned an invalid type. The function must "
        "either return a dictionary of metric names to mean, sem tuples "
        "or a single mean, sem tuple, or a single mean."
    )


def run_trial(exp, trial, func, **kwargs) -> Data:
    assert trial.status != TrialStatus.COMPLETED, "already evaluated"
    return eval_trial(exp, trial, func, kwargs)


def eval_exp(exp, func, **kwargs) -> Data:
    # return new data
    return Data.from_multiple_data(
        [
            eval_trial(exp, trial, func, kwargs)
            for trial in exp.trials.values()
            if trial.status != TrialStatus.COMPLETED
        ]
    )


def get_size(data):
    if data != None:
        return len(data._df.index)  # #key * #trial
    else:
        return 0


def get_non_dominated(exp):

    df = exp.fetch_data().df
    arms = exp.arms_by_name

    pareto_set = []
    for key in exp.metrics:
        tmp_df = df.loc[df['metric_name'] == key].sort_values('mean')
        # print(tmp_df)
        try:
            arm_name = tmp_df.values[0][0]
            arm = arms.get(arm_name)
            params = arm.parameters
            arg_str = [str(i) for i in arm.parameters.values()]
            tag = '_'.join(arg_str)
            val = (tag, tmp_df.values[0][2])
            pareto_set.append({key: (val, params)})
        except Exception as e:
            print(e)
            break
    return pareto_set


def draw_optimization_trace(exp):
    # not tested yet
    """Retrieves the plot configuration for optimization trace, which shows
    the evolution of the objective mean over iterations.

    Args:
        objective_optimum: Optimal objective, if known, for display in the
            visualization.
    """
    if not exp.trials:
        raise ValueError("Cannot generate plot as there are no trials.")

    for metric in exp.optimization_config.objective.metrics:
        objective_name = metric.name
        best_objectives = np.array(
            [
                [
                    checked_cast(Trial, trial).get_metric_mean(objective_name)
                    for trial in list(exp.trials.values())[1:]
                    if trial.status.is_completed
                ]
            ]
        )
        hover_labels = [
            _format_dict(not_none(checked_cast(Trial, trial).arm).parameters)
            for trial in list(exp.trials.values())[1:]
            if trial.status.is_completed
        ]

        config = optimization_trace_single_method(
            y=(
                np.minimum.accumulate(best_objectives, axis=1)
                if exp.optimization_config.objective.minimize
                else np.maximum.accumulate(best_objectives, axis=1)
            ),
            # optimum=objective_optimum,
            title="Model performance vs. # of iterations",
            ylabel=objective_name.capitalize(),
            hover_labels=hover_labels,
        )

        render(config)
