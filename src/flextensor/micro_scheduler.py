from flextensor.scheduler import schedule
from flextensor.task import register_task
from flextensor.utils import RpcInfo
# from flextensor.ppa_model import measure_latency
from flextensor.intrinsic import register_intrin

def gen_micro_schedule(task, target, model_func=None):
    register_task(task, override=True)
    # register_intrin(intrin, override=True)
    rpc_info = RpcInfo(None, None)
    rpc_info.target = target 
    s, bufs, config = schedule(
        task.key,
        slevel=2, rlevel=2,
        parallel=8,
        op_trial=10,
        model_measurer=model_func,
        rpc_info=rpc_info,
        warm_up_epoch=2, warm_up_number=8
    ) 
    return s, bufs
