intrinsic_lib = ["GEMV", "GEMM", "DOT", "CONV"]

eval_methods = ["Model", "Profile", "Simulate"] 

all_metrics = ["latency", "throughput", "power", "area"]

supported_models = ["ResNet50", "MobileNetV2", "Xception"]

bits_map = {"int8": 8, "float16": 16, "float32": 32, "int32": 32}

maestro_home = "~/HASCO/src/maestro/"  # absolute path 

model_path = maestro_home + "maestro"

rst_dir = "./rst/"

model_config_dir = "./config/"

mapping_dir = "./mapping/"

sw_dir = rst_dir+"./software/"

verbose = False 