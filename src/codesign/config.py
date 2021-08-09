intrinsic_lib = ["GEMV", "GEMM", "DOT", "CONV"]

def check_intrinsic(ty):
    return ty.startswith(tuple(intrinsic_lib))

eval_methods = ["Model", "Profile", "Simulate"] 

all_metrics = ["latency", "throughput", "power", "area"]

supported_models = ["ResNet50", "MobileNetV2", "Xception"]

bits_map = {"int8": 8, "float16": 16, "float32": 32, "int32": 32}

maestro_home = "~/work/HASCO/src/maestro/"  # absolute path

maestro_path = maestro_home + "maestro"

tenet_path = "~/work/HASCO/src/TENET/tenet"  # TODO: stub

rst_dir = "./rst/"

model_config_dir = "./config/"

mapping_dir = "./mapping/"

sw_dir = rst_dir+"./software/"

verbose = False 

import os
for path in [rst_dir, rst_dir + model_config_dir, rst_dir + mapping_dir, sw_dir]:
    if not os.path.exists(path) or not os.path.isdir(path):
        os.mkdir(path)
