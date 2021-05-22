import csv
import numpy as np
import random
import os 
import subprocess

from fnmatch import fnmatchcase as match
from inspect import signature

from codesign.config import  verbose, rst_dir, bits_map
from hw_generator.generator import parse_params
from codesign.flextensor_extend import parse_schedule
from benchmark.benchmark import Workload
from benchmark.computations import ttm_compute, gemv_compute

from utils.logger import logger



def gen_config(path, params, acc_type, tag):

    x, y, sp_kb, sp_banks, _, _, local_kb, _, dtype = parse_params(acc_type, params) # off-chip memory are not modeled

    pes = x * y

    bw = 2 * sp_banks * bits_map[dtype]  # dual ports 
    filename = path + "accelerator_" + tag + ".m"
    fp = open(rst_dir +filename, "w+")
    fp.write("NumPEs: " + str(pes))
    fp.write("\nL1Size: " + str(local_kb * 1024))   # using bytes
    fp.write("\nL2Size: " + str(sp_kb * 1024))  # using bytes
    fp.write("\nNoC_BW: " + str(bw))
    fp.close()
    return filename



class PPAModel:

    def __init__(self, lib_path, config_file):
        self.func = lib_path
        self.config_file = config_file
        self.max_val = float("inf")  # to avoid deviding by 0
        self.min_val = float("-inf")



    def generate_dsfl(self, loop_info, acc, all_dims, directives):

        px, py, _, _, _, _, _, dataflow, _ = parse_params(acc.type, acc.params)
        pe = str(int(px) * int(py))

        uninvolved_dims = all_dims    

        for idx in loop_info['inner']:
            uninvolved_dims.discard(idx['origin'].upper())

        if acc.type == "GEMM":
            '''handle GEMM accelerator dataflows'''
            # print(schedule)

            if dataflow == "OS": 
                '''OS dataflow'''

                for dim in uninvolved_dims:
                    directives.append(f"TemporalMap(1, 1) {dim};\n")

                directives.append(f"TemporalMap({loop_info['inner'][1]['length']}, {py}) {loop_info['inner'][1]['origin'].upper()};\n")
                directives.append(f"SpatialMap({loop_info['inner'][0]['length']}, {px}) {loop_info['inner'][0]['origin'].upper()};\n")
                directives.append(f"TemporalMap({loop_info['inner'][2]['length']}, {loop_info['inner'][2]['length']}) {loop_info['inner'][2]['origin'].upper()};\n")

                directives.append(f"Cluster({pe}, P);\n")
                directives.append(f"TemporalMap({loop_info['inner'][2]['length']}, {loop_info['inner'][2]['length']}) {loop_info['inner'][2]['origin'].upper()};\n")
                directives.append(f"SpatialMap(1, 1) {loop_info['inner'][1]['origin'].upper()};\n")
                directives.append(f"SpatialMap(1, 1) {loop_info['inner'][0]['origin'].upper()};\n")

                return 
            else:     
                '''WS dataflow'''

                for dim in uninvolved_dims:
                    directives.append(f"TemporalMap(1, 1) {dim};\n")

                directives.append(f"TemporalMap({loop_info['inner'][1]['length']}, {py}) {loop_info['inner'][1]['origin'].upper()};\n")
                directives.append(f"SpatialMap({loop_info['inner'][0]['length']}, {px}) {loop_info['inner'][0]['origin'].upper()};\n")
                directives.append(f"TemporalMap({loop_info['inner'][2]['length']}, {loop_info['inner'][2]['length']}) {loop_info['inner'][2]['origin'].upper()};\n")
        
                directives.append(f"Cluster({loop_info['inner'][2]['length']}, P);\n")
                directives.append(f"TemporalMap({py}, {py}) {loop_info['inner'][1]['origin'].upper()};\n")
                directives.append(f"TemporalMap({px}, {px}) {loop_info['inner'][0]['origin'].upper()};\n")
                directives.append(f"SpatialMap(1, 1) {loop_info['inner'][2]['origin'].upper()};\n")

                return


        elif acc.type == "CONV":
            '''
            NVDLA-style dataflow
            Temporal_Map(3,3) R
            Temporal_Map(3,3) S
            Temporal_Map(64,64) C
            Temporal_Map(1,1) X
            Temporal_Map(1,1) Y
            Cluster(64, PE)
            Spatial_Map(1,1) K
            '''

            directives.append(f"SpatialMap(1 ,1) N;\n")
            directives.append(f"TemporalMap(3 ,3) R;\n")
            directives.append(f"TemporalMap(3, 3) S;\n")
            directives.append(f"TemporalMap({pe}, {pe}) C;\n")
            directives.append(f"TemporalMap(1, 1) X;\n")
            directives.append(f"TemporalMap(1, 1) Y;\n")
            directives.append(f"Cluster({pe}, P);\n")
            directives.append(f"SpatialMap(1, 1) K;\n")

            return 
            
        elif acc.type == "GEMV":
            
            for dim in uninvolved_dims:
                directives.append(f"TemporalMap(1, 1) {dim};\n")
            
            directives.append(f"SpatialMap({loop_info['inner'][0]['length']}, {pe}) {loop_info['inner'][0]['origin'].upper()};\n")
            directives.append(f"TemporalMap({loop_info['inner'][1]['length']}, {loop_info['inner'][1]['length']}) {loop_info['inner'][1]['origin'].upper()};\n")
    
            directives.append(f"Cluster({loop_info['inner'][1]['length']}, P);\n")
            directives.append(f"TemporalMap({pe}, {pe}) {loop_info['inner'][0]['origin'].upper()};\n")
            directives.append(f"SpatialMap(1, 1) {loop_info['inner'][1]['origin'].upper()};\n")


            return 

        elif acc.type == "DOT": 

            directives.append(f"SpatialMap(1, 1) {uninvolved_dims.pop()};\n")

            for dim in uninvolved_dims:
                directives.append(f"TemporalMap(1, 1) {dim};\n")
            
            directives.append(f"TemporalMap({loop_info['inner'][1]['length']}, {loop_info['inner'][1]['length']}) {loop_info['inner'][1]['origin'].upper()};\n")
    
            directives.append(f"Cluster({loop_info['inner'][1]['length']}, P);\n")
            directives.append(f"SpatialMap(1, 1) {loop_info['inner'][1]['origin'].upper()};\n")
            return




    def generate_single_mapping(self, workload, schedule, acc, directives): 

        loop_info = parse_schedule(schedule) 

        directives.append("Layer " + workload.name + " {\n")
        directives.append("Type: CONV \n")  # due to the model, all workloads expressed as conv
        dims = set(['N', 'C', 'Y', 'X', 'K', 'R', 'S'])

        if workload.type in ["CONV", "DWCONV"]:
            directives.append("Stride { X: " + str(workload.args[7]) + ", Y: " + str(workload.args[7]) + " }\n") 
        
        directives.append("Dimensions { ") 
        if workload.type in ["CONV", "DWCONV"]:
            arg_names = signature(workload.compute).parameters
            # print(type(arg_names))
            line = ""
            for (val, name) in zip(workload.args[:7], arg_names):
                line += " " + name + ": " + str(val) + ", "
            directives.append(line)

        elif workload.type in ["GEMM", "GEMV"]:
            line = " K: " + str(workload.args[0]) + ", Y: " + str(workload.args[1]) + ", C: " + str(workload.args[2])
            for dim in ['N', 'X', 'R', 'S']:
                line += " " + dim + ": 1, " 
            directives.append(line)

        elif workload.type == "TTM":
            line = " K: "  + str(workload.args[2]) + ", Y: " + str(workload.args[0]) +", X: " + str(workload.args[1]) + ", C: " + str(workload.args[3])
            for dim in ['N', 'X', 'R', 'S']:
                line += " " + dim + ": 1, " 
            directives.append(line)
            
        else:
            pass
        
        directives.append(" }\n")

        directives.append("Dataflow {\n")

        self.generate_dsfl(loop_info, acc, dims, directives)
        
        directives.append("}\n")
        directives.append("}\n")




    def evaluate(self, benchmark, schedules, acc, mapping_file):
        if schedules == None:
            return self.max_val, self.min_val, self.max_val, self.max_val, self.max_val
        if not isinstance(schedules, list):
            schedules = [schedules] 

        '''generate mapping files'''
        mapping_fp = open(rst_dir + mapping_file, "w+")
        mapping_fp.write("Network " + benchmark.name + " {\n")
        for (wl, s) in zip(benchmark.workloads, schedules):
            directives = []
            if wl.type != "MTTKRP" :  
                self.generate_single_mapping(wl, s, acc, directives)
            else: # special process for mttkrp 
                m, n, k, l, dtype, layout = wl.args
                if wl.stage != 2:
                    s1 = s[0] if wl.stage == 0 else s
                    ttm_wl = Workload(wl.name +"_stage1", "TTM",  ttm_compute, (m, l, n, k, dtype, layout) )
                    self.generate_single_mapping(ttm_wl, s1, acc, directives)
                if wl.stage != 1:
                    s2 = s[1] if wl.stage == 0 else s
                    gemv_wl = Workload(wl.name +"_stage2", "GEMV", gemv_compute, (m, n, l, dtype, layout) )
                    self.generate_single_mapping(gemv_wl, s2, acc, directives)

            for line in directives:
                mapping_fp.write(line)
        mapping_fp.write("}\n")
        mapping_fp.close() 

        '''call extern model binary'''
        param_list = [ 
            self.func,
            "--print_res=false",
            "--print_res_csv_file=true",
            "--print_log_file=false",
            "--Mapping_file="+ mapping_file,
            "--HW_file=" + self.config_file,
            "--print_design_space=true",
            "--msg_print_lv=0"
        ]
 
        devNull = open(os.devnull, 'w') 
        p = subprocess.Popen(''.join(p+' ' for p in param_list), shell=True, cwd=rst_dir, stdout = devNull,  stderr=devNull)
        p.wait()


        result_csv = rst_dir + mapping_file.split('/')[-1].replace(".m", ".csv")
        
        if not os.path.exists(result_csv): 
            os.remove(rst_dir + mapping_file) 
            return self.max_val, self.min_val, self.max_val, self.max_val, self.max_val

        '''read the CSV file to obtain ppa data'''
        latency = []
        ops = []
        power = []
        energy = []
        area = []
        with open(result_csv, "r") as f:
            reader = list(csv.reader(f))
            for row in reader[1:]:
                runtime = int(row[3])
                latency.append(runtime)
                energy.append(float(row[4]))
                ops.append(float(row[5]) * runtime)
                area.append(float(row[7]))
                power.append(float(row[8]))
        
        if not verbose: 
            os.remove(rst_dir + mapping_file)
            os.remove(result_csv)

        total_runtime = np.sum(latency)
        total_ops = np.sum(ops)
        avg_pow = np.mean(power)
        total_energy = np.sum(energy)
        max_area = np.max(area)
        '''add some randomness'''
        rand_factor = 0.03
        total_runtime += random.uniform(0, rand_factor * total_runtime)
        total_ops += random.uniform(0, rand_factor * total_ops)
        avg_pow += random.uniform(0, rand_factor * avg_pow)
        total_energy += random.uniform(0, rand_factor * total_energy)
        max_area +=  random.uniform(0, rand_factor * max_area)
        return total_runtime, total_ops / total_runtime, avg_pow, total_energy, max_area
        

