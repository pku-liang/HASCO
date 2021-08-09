import tvm
from flextensor.intrinsic import Intrinsic, register_intrin


def parse_params(acc_type, params): 
    if isinstance(params, list):
        if len(params) == 9:  # current #params
            return params
        else:
            x = params[0]
            params.insert(1, x)
            return params
    else:
        x = params.get(f"x")
        y = x if params.get(f"y") == None else params.get(f"y") 
        sp_cap = params.get(f"sp_capacity")
        sp_banks = params.get(f"sp_banks")
        dma_width = params.get(f"dma_buswidth")
        dma_bytes = params.get(f"dma_maxbytes")
        l_cap = params.get(f"local_capacity")
        dtype = params.get(f"dtype")
        if acc_type == "GEMM":
            dataflow = params.get(f"dataflow") 
        else:
            dataflow = "FIXED"
        return x, y, sp_cap, sp_banks, dma_width, dma_bytes, l_cap, dataflow, dtype



class generator:

    def __init__(self, type, intrin_func, interface_func, stt_matrix, dtype="int8"):
        self.type = type + ("" if stt_matrix is None else "-TensorLib")
        self.intrin_func = intrin_func
        self.intf_func = interface_func
        self.stt_matrix = stt_matrix
        self.dtype = dtype

    def meet_constraints(self):
        return

    def instantiate(self):
        return


class accelerator:
    
    def __init__(self, generator, acc_interface, params, tag, intrin_args):
        self.type = generator.type
        self.stt_matrix = generator.stt_matrix
        self.name = generator.type + "_" + tag
        self.intrin_func = generator.intrin_func
        self.target = "c -device=micro_dev"
        self.flex_intrin = Intrinsic(self.type, self.name, self.intrin_func, intrin_args,
                   acc_interface, self.target)
        register_intrin(self.flex_intrin)
        self.params = params

    def add_intrinsic(self, intrin_func, intrin_args, interface):
        flex_intrin = Intrinsic("", "", intrin_func, intrin_args,
                   interface, self.target)  # should be a intrin list
        register_intrin(flex_intrin)


    def print_info(self):
        print(self.name)
        print(self.params)
        
