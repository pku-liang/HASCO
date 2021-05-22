import re
from matplotlib.cm import  ScalarMappable
import matplotlib.pyplot as plt
import numpy as np

def normalize(x):
    norm = np.linalg.norm(x)
    if norm==0:
        return x
    return x / norm

def find_lpa(log):
    latency = []
    power = []
    area = []
    tags = []
    with open(log, 'r') as f:
        for line in f.readlines():
            lpa_pattern = r"[']latency.*[)]"
            result = re.search(lpa_pattern, line)
            tag_pattern = r".*?\s"
            tag = re.search(tag_pattern, line)
            if result is not None:
                str_dict = eval('{'+result.group()+'}')
                print(str_dict)
                print(tag)
                if str_dict['latency']=='100000000000':
                    continue
                latency.append(str_dict['latency'][0])
                area.append(str_dict['area'][0])
                power.append(str_dict['power'][0]) 
                tags.append(tag.group())
    return tags, normalize(latency), normalize(power), normalize(area)


def parse_params(tags):
    param_list = [[] for i in range(6)]
    for tag in tags:
        params = tag.split('_')
        pes = eval(params[0] + '*' + params[1])
        param_list[0].append(pes)
        buf_cap = eval(params[2] + '+' + params[7])
        param_list[1].append(buf_cap)
        for i in range(2, 6):
            param_list[i].append(params[i+1])
    return param_list[0], param_list[1], param_list[2], param_list[3], param_list[4], param_list[5]



def draw_pareto_scatter(latency, power, area):
    figs, axes = plt.subplots(1, 3, figsize = (17, 5))
    cm = plt.cm.get_cmap('viridis')
    axes[0].scatter(latency, power)
    axes[0].set_xlabel('latency')
    axes[0].set_ylabel('power')
    # axes[0].set_xlim(0, 1e-7)
    # axes[0].set_ylim(0, 1e-2)

    axes[1].scatter(latency, area)
    axes[1].set_xlabel('latency')
    axes[1].set_ylabel('area')
    # axes[1].set_xlim(0, 1e-7)
    # axes[1].set_ylim(0, 1e-8)

    axes[2].scatter(area, power)
    axes[2].set_xlabel('area')
    axes[2].set_ylabel('power')
    # axes[2].set_xlim(0, 5e-4)
    # axes[2].set_ylim(0, 1e-8)
    plt.show()



def reorganize_data(pes, buf_cap, latency, power, area):
    pe_set = list(set(pes))
    pe_set.sort() 
    buf_set = list(set(buf_cap))
    buf_set.sort()
    latency2D = np.zeros((len(pe_set),len(buf_set)))
    power2D = np.zeros((len(pe_set),len(buf_set)))
    area2D = np.zeros((len(pe_set),len(buf_set)))

    pe_dict = {}
    buf_dict = {}
    for i in range(len(pe_set)):
        pe = pe_set[i]
        pe_dict[pe] = i
    
    for i in range(len(buf_set)):
        buf = buf_set[i]
        buf_dict[buf] = i

    for i in range(len(latency)):
        pe_idx = pe_dict[pes[i]]
        buf_idx = buf_dict[buf_cap[i]]
        latency2D[pe_idx][buf_idx] = latency[i]
        power2D[pe_idx][buf_idx] = power[i]
        area2D[pe_idx][buf_idx] = area[i]

    return pe_set, buf_set, latency2D, power2D, area2D



def draw_isograph(pes, buf_cap, latency, power, area):
    pes = [16, 32]
    figs, axes = plt.subplots(1, 3, figsize = (17, 5))
    X, Y = np.meshgrid(buf_cap, pes)

    axes[0].contourf(X, Y, latency, levels=15, linestyles='solid')
    axes[0].title.set_text('Latency')
    axes[0].set_xlabel('Bufs')
    axes[0].set_ylabel('PEs')


    axes[1].contourf(X, Y, power, levels=15, linestyles='solid')
    axes[1].title.set_text('Power')
    axes[1].set_xlabel('Bufs')
    axes[1].set_ylabel('PEs')

    axes[2].contourf(X, Y, area, levels=15, linestyles='solid')
    axes[2].title.set_text('Area')
    axes[2].set_xlabel('Bufs')
    axes[2].set_ylabel('PEs')

    plt.show()



if __name__=='__main__':
    tags, latency, power, area = find_lpa('logs/xception_groundtruth_pp.log')
    print(latency)
    draw_pareto_scatter(latency, power, area)

    pes, buf_cap, sp_banks, dma_width, dma_bytes, dataflow = parse_params(tags)

    pes, buf_cap, latency, power, area = reorganize_data(pes, buf_cap, latency, power, area)
    draw_isograph(pes, buf_cap, latency, power, area)