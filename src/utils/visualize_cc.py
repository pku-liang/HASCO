import re
from matplotlib.cm import  ScalarMappable
import matplotlib.pyplot as plt
import numpy as np

def normalize(x):  
    norm = np.linalg.norm(x)
    if norm==0:
        return x
    val =  x / (0.01 * norm)
    print(val.min(),  val.max())
    y = 1.0 / (1 + 0.1*np.exp(-val))
    print(y.min(),  y.max())
    return -y

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
                params = tag.group().split('_')
                if params[2] != "1024":
                    continue
                if str_dict['latency']=='100000000000':
                    continue
                latency.append(str_dict['latency'][0])
                area.append(str_dict['area'][0])
                power.append(str_dict['power'][0]) 
                tags.append(tag.group())
    print(min(latency), "~~~~", min(power), "~~~~~", min(area)) 
    return tags, normalize(latency), normalize(power), normalize(area)


def parse_params(tags):
    param_list = [[] for i in range(5)]
    count = 0
    for tag in tags:
        params = tag.split('_')
        if params[2] != "1024":
            continue
        pes = eval(params[0])
        param_list[0].append(pes)
        buf_cap = eval(params[2])
        param_list[1].append(buf_cap)
        for i in range(2, 5):
            param_list[i].append(eval(params[i+1]))
    return param_list[0], param_list[1], param_list[2], param_list[3], param_list[4]


def draw_pareto_scatter(latency, power, area):

    SMALL_SIZE = 20
    MEDIUM_SIZE = 22
    BIGGER_SIZE = 24

    plt.rc('font', size=SMALL_SIZE)          # controls default text sizes
    plt.rc('axes', titlesize=SMALL_SIZE)     # fontsize of the axes title
    plt.rc('axes', labelsize=MEDIUM_SIZE)    # fontsize of the x and y labels
    plt.rc('xtick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('ytick', labelsize=SMALL_SIZE)    # fontsize of the tick labels
    plt.rc('legend', fontsize=SMALL_SIZE)    # legend fontsize
    plt.rc('figure', titlesize=BIGGER_SIZE)  # fontsize of the figure title


    figs, axes = plt.subplots(1, 3, figsize = (19, 7))
    #figs.tight_layout(pad=1.5)    

    cm = plt.cm.get_cmap('viridis')
    axes[0].scatter(latency, power)
    axes[0].set_xlabel('normalized latency')
    axes[0].set_ylabel('normalized power')
    axes[0].tick_params(axis="y",direction="in", pad=-50)
    axes[0].text(0.1, -0.05, '(a) latency-power', ha="center")
    # axes[0].set_xlim(0, 1e-7)
    # axes[0].set_ylim(0, 1e-2)

    axes[1].scatter(latency, area)
    axes[1].set_xlabel('normalized latency')
    axes[1].set_ylabel('normalized area')
    axes[1].tick_params(axis="y",direction="in", pad=-40)
    axes[1].text(0.1, -0.06, '(b) latency-area', ha="center")
    # axes[1].set_xlim(0, 1e-7)
    # axes[1].set_ylim(0, 1e-8)

    axes[2].scatter(area, power)
    axes[2].set_xlabel('normalized area')
    axes[2].set_ylabel('normalized power')
    axes[2].tick_params(axis="y",direction="in", pad = -50)
    axes[2].text(0.1, -0.05, '(c) area-power', ha="center")
    # axes[2].set_xlim(0, 5e-4)
    # axes[2].set_ylim(0, 1e-8)
    plt.show()
    #figs.savefig("ppa.pdf", bbox_inches='tight')


def reorganize_data(x, y, latency, power, area):
    x_set = list(set(x))
    x_set.sort() 
    y_set = list(set(y))
    y_set.sort()
    latency2D = np.zeros((len(x_set),len(y_set)))
    power2D = np.zeros((len(x_set),len(y_set)))
    area2D = np.zeros((len(x_set),len(y_set)))

    x_dict = {}
    y_dict = {}
    for i in range(len(x_set)):
        tmp_x = x_set[i]
        x_dict[tmp_x] = i
    
    for i in range(len(y_set)):
        tmp_y = y_set[i]
        y_dict[tmp_y] = i

    for i in range(len(latency)):
        x_idx = x_dict[x[i]]
        y_idx = y_dict[y[i]]
        latency2D[x_idx][y_idx] = latency[i]
        power2D[x_idx][y_idx] = power[i]
        area2D[x_idx][y_idx] = area[i]

    return x_set, y_set, latency2D, power2D, area2D



def draw_isograph(pes, banks, latency, power, area):
    
    figs, axes = plt.subplots(1, 3, figsize = (17, 5))
    figs.tight_layout(pad=2)    

    X, Y = np.meshgrid(banks, pes) 

    axes[0].contourf(X, Y, latency, levels=10, linestyles='solid')
    axes[0].text(2.5, -0.05, '(a) Latency')
    axes[0].set_xlabel('Banks')
    axes[0].set_ylabel('PEs')


    axes[1].contourf(X, Y, power, levels=10, linestyles='solid')
    axes[1].text(2.5, -0.05,'(b) Power')
    axes[1].set_xlabel('Banks')
    axes[1].set_ylabel('PEs')

    axes[2].contourf(X, Y, area, levels=10, linestyles='solid')
    axes[2].text(2.5, -0.05, '(c) Area')
    axes[2].set_xlabel('Banks')
    axes[2].set_ylabel('PEs')

    plt.show()
   



if __name__=='__main__':
    tags, latency, power, area = find_lpa('logs/cc_xception_groundtruth.log')
   
    # draw_pareto_scatter(latency, power, area)
# '''
    pes, buf_cap, sp_banks, dma_width, dma_bytes = parse_params(tags)
    pes, sp_banks, latency2D, power2D, area2D = reorganize_data(pes, sp_banks, latency, power, area)
    print(pes)
    print(sp_banks)

    draw_isograph(pes, sp_banks, latency2D, power2D, area2D)
# '''
