import re
from matplotlib.cm import  ScalarMappable
import matplotlib.pyplot as plt
import numpy as np
 
def extract_lpa(old_log, new_log):  

    with open(old_log, 'r') as f:
        with open(new_log, 'w') as nf:
            for line in f.readlines():
                pattern = r"[']latency.*[)]"
                result = re.search(pattern, line)
                tag_pattern = r".*?\s"
                tag = re.search(tag_pattern, line)
                if result is not None:
                    print(tag.group())
                    str_dict = eval('{'+result.group()+'}')
                    print(str_dict)
                    if str_dict['latency']=='100000000000':
                        continue
                    power = float(str_dict['power'][0]) * 6
                    str_dict['power'] = (power, 0.0)
                    nf.write(tag.group())
                    nf.write(str(str_dict))
                    nf.write("\n")


if __name__=='__main__':
    extract_lpa('logs/xception_groundtruth.log', 'logs/xception_groundtruth_pp.log')