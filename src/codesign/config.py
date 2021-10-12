import os
intrinsic_lib = ["GEMV", "GEMM", "DOT", "CONV"]


def check_intrinsic(ty):
    return ty.startswith(tuple(intrinsic_lib))


# Methods for DSE, only Model is supported
eval_methods = ["Model", "Profile", "Simulate"]

# The metrics supported by the DSE
all_metrics = ["latency", "throughput", "power", "area"]

# We tested these three models, other models in Keras may be supported
supported_models = ["ResNet50", "MobileNetV2", "Xception"]

# The bitwidth of each dtype
bits_map = {"int8": 8, "float16": 16, "float32": 32, "int32": 32}

# The path to hold results
rst_dir = os.path.join(os.getcwd(), "rst/")

# The path to the home directory of Maestro
maestro_home = "~/work/HASCO/src/maestro/"  # absolute path

# The path to the executables of Maestro
maestro_path = maestro_home + "maestro"

# The path to the interface executable of TENET
tenet_path = "~/TENET/bin/HASCO_interface"  # TODO: stub

# The paths to store the input files for TENET
tenet_input_dir = os.path.join(rst_dir, "TENET/")
tenet_mapping_dir = os.path.join(tenet_input_dir, "mapping/")
tenet_pe_array_dir = os.path.join(tenet_input_dir, "pe_array/")
tenet_statement_dir = os.path.join(tenet_input_dir, "statement/")

# Params to conver TENET output into metrics
tenet_param = {
    "avg_latency": 8,  # Avg latency for data transfer
    "f_trans": 12,  # Power per element transferred
    "f_work": 4  # Power per element in the workload
}

# The path to the home directory that holds TensorLib
tensorlib_home = "~/TensorLib/"  # TODO: stub

# The main class of TensorLib
tensorlib_main = "tensorlib.ParseJson"

# The path to hold config for Masestro
model_config_dir = "config/"

# The path to hold mappings for Maestro
mapping_dir = "mapping/"

# The paths to the output directories
sw_dir = os.path.join(rst_dir, "software/")
hw_dir = os.path.join(rst_dir, "hardware/")

verbose = False

for path in [rst_dir, os.path.join(rst_dir, model_config_dir), os.path.join(rst_dir, mapping_dir), sw_dir]:
    if not os.path.exists(path) or not os.path.isdir(path):
        os.mkdir(path)
