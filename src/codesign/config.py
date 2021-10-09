import os
intrinsic_lib = ["GEMV", "GEMM", "DOT", "CONV"]


def check_intrinsic(ty):
    return ty.startswith(tuple(intrinsic_lib))


eval_methods = ["Model", "Profile", "Simulate"]

all_metrics = ["latency", "throughput", "power", "area"]

supported_models = ["ResNet50", "MobileNetV2", "Xception"]

bits_map = {"int8": 8, "float16": 16, "float32": 32, "int32": 32}

rst_dir = os.path.join(os.getcwd(), "rst/")

maestro_home = "~/work/HASCO/src/maestro/"  # absolute path

maestro_path = maestro_home + "maestro"

tenet_path = "~/TENET/bin/HASCO_interface"  # TODO: stub

tenet_input_dir = os.path.join(rst_dir, "TENET/")
tenet_mapping_dir = os.path.join(tenet_input_dir, "mapping/")
tenet_pe_array_dir = os.path.join(tenet_input_dir, "pe_array/")
tenet_statement_dir = os.path.join(tenet_input_dir, "statement/")
# tenet_experiment_dir = os.path.join(tenet_input_dir, "experiment/")

tenet_param = {
    "avg_latency": 8,
    "f_trans": 12,
    "f_work": 4
}

tensorlib_home = "~/TensorLib/"  # TODO: stub

tensorlib_main = "tensorlib.ParseJson"


model_config_dir = "config/"

mapping_dir = "mapping/"


sw_dir = os.path.join(rst_dir, "software/")
hw_dir = os.path.join(rst_dir, "hardware/")

verbose = False

for path in [rst_dir, os.path.join(rst_dir, model_config_dir), os.path.join(rst_dir, mapping_dir), sw_dir]:
    if not os.path.exists(path) or not os.path.isdir(path):
        os.mkdir(path)
