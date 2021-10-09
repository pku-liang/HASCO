#!/bin/python3

import sys
sys.path.append("./src/")
sys.path.append("./src/Ax/")

import argparse
import json

from hw_generator.generator_conv import CONVGenerator
from hw_generator.generator_gemm import GEMMGenerator

from benchmark.benchmark import BenchmarkCNN
from codesign.explorer import codesign

JSONFORMAT = """
design space specification JSON file format:
{
    "stts":{
        <name>:<2D-array-stt>,
        ...
    },
    "hw_space":{
        "x":[<choices-for-width-of-PE-array>],
        "y":[<choices-for-height-of-PE-array>],
        "dma_buswidth":[<choices-for-bandwidth>],
        "dataflow":[<names-in-stts>]
    }
}
"""

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        usage="HASCO CommandLine Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=JSONFORMAT + 'Contact semiwaker@pku.edu.cn for bugs')
    parser.add_argument('-i', '--intrinsic', type=str, choices=["CONV", "GEMM"],
                        required=True, help="the type of hardware intrinsic (GEMM/CONV)")
    parser.add_argument('-b', '--benchmark', type=str,
                        required=True, help="the benchmark")
    parser.add_argument('-f', '--file', type=str, required=True,
                        help="the JSON file that describes the design space")
    parser.add_argument('-l', '--latency', type=int, default=1000,
                        help="constraints on latency")
    parser.add_argument('-p', '--power', type=int, default=20,
                        help="constraints on power")
    parser.add_argument('-a', '--area', type=int, default=1,
                        help="constraints on area")
    parser.add_argument('--init', type=int, default=10,
                        help="number of initial trails")
    parser.add_argument('--iter', type=int, default=20,
                        help="number of iterative trails")
    parser.add_argument('--dtype', type=str, default="int8",
                        help="dtype of the instinct")
    parser.add_argument('--method', type=str, default="Model",
                        help="method for the DSE (Model/Profile/Simulate), Currently only Model is supported")

    args = parser.parse_args()

    with open(args.file, "r", encoding="utf-8") as fin:
        x = json.load(fin)
        stts = x["stts"]
        hw_space = x["hw_space"]

    if args.intrinsic == "CONV":
        generator = CONVGenerator(stts, hw_space, args.dtype)
    else:
        generator = GEMMGenerator(stts, hw_space, args.dtype)

    benchmark = BenchmarkCNN(args.benchmark, args.dtype, layout=generator.type)

    constraints = {"latency": args.latency,
                   "power": args.power, "area": args.area}  # TODO

    print(f"[HASCO] Testing accelerators with {args.intrinsic} intrinsic ...")
    codesign(benchmark, generator, args.method,
             constraints, init_size=args.init, trial_num=args.trail)
    print("[HASCO] Passed.")
