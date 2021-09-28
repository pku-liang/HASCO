import json
import subprocess
import os

import tvm
from flextensor.intrinsic import Intrinsic, register_intrin
from codesign.config import tensorlib_home, tensorlib_main, bits_map, rst_dir


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
        dataflow = params.get(f"dataflow")
    return x, y, sp_cap, sp_banks, dma_width, dma_bytes, l_cap, dataflow, dtype


class generator:

    def __init__(self, type, intrin_func, interface_func, stt_matrix, hw_space, dtype="int8"):
        self.type = type
        self.intrin_func = intrin_func
        self.intf_func = interface_func
        self.stt_matrix = stt_matrix
        self.hw_space = hw_space
        self.dtype = dtype

    def meet_constraints(self):
        return

    def instantiate(self):
        return


class accelerator:

    def __init__(self, generator, intrin_size, acc_interface, params, tag, intrin_args):
        self.type = generator.type
        self.stt_matrix = generator.stt_matrix
        self.name = generator.type + "_" + tag
        self.intrin_func = generator.intrin_func
        self.intrin_size = intrin_size
        self.target = "c -device=micro_dev"
        self.flex_intrin = Intrinsic(self.type, self.name, self.intrin_func, intrin_args,
                                     acc_interface, self.target)
        register_intrin(self.flex_intrin)
        self.params = params

    def generate_hardware(self, key):
        if self.stt_matrix is not None:
            tensorlib_input = {
                "benchmark": self.type,
                "bitwidth": bits_map[self.params["dtype"]],
                "length": self.intrin_size,
                "STT": self.stt_matrix[self.params["dataflow"]]
            }

            if not os.path.exists(os.path.join(rst_dir, "hardware")):
                os.mkdir(os.path.join(rst_dir, "hardware"))

            input_file = os.path.join(
                rst_dir, f"hardware/{self.name}_{key}.json")
            output_file = os.path.join(
                rst_dir, f"hardware/{self.name}_{key}.v")

            with open(input_file, "w") as fout:
                json.dump(tensorlib_input, fout, indent=4)

            try:
                subprocess.run(
                    [f'(cd {tensorlib_home}; sbt "run {tensorlib_main} {input_file} {output_file}")'])
            except Exception as e:
                print(e)

    def add_intrinsic(self, intrin_func, intrin_args, interface):
        flex_intrin = Intrinsic("", "", intrin_func, intrin_args,
                                interface, self.target)  # should be a intrin list
        register_intrin(flex_intrin)

    def print_info(self):
        print(self.name)
        print(self.params)
