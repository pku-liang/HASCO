# HASCO


## Introduction
Tensor computation is fundamental for many scientific and engineering applications, such as machine learning, data mining, quantum chemistry. Though dedicated hardware and software optimizations have progressed considerably for tensor computation, they primarily focus on either the hardware part or the software part. Optimizing the two parts in isolation inevitably suffers from sub-optimal solutions confined in a local design space. 

While seemingly appealing, there has been less attention on hardware/software co-design for tensor computation. This is largely because the design of hardware and software components influence each other, and the joint design space can be huge. A general approach to tackle the co-design problem is to develop a unified intermediate representation (IR), based on which designers can partition the hardware and software, optimize, and synthesize the hardware and software. However, developing such a general IR and synthesizing arbitrary hardware are challenging. 

We provide a co-design approach specific to tensor computation —— HASCO. As tensor computation can be described using nested loops, we naturally embed loop information into our IR design for tensor computation partitioning, optimization, and implementation. A subset of the loops are implemented using spatial hardware accelerators, and the remaining loops are implemented using software programs. The fundamental questions are: 1) how to define the interface between the hardware accelerators and the software programs, 2) how to navigate the huge design space for each part. HASCO solves these questions with efficient algorithms. 



## Installation

Requires: Python >= 3.5,
          packages (numpy, tqdm, json, csv),
          [Ax](https://github.com/facebook/Ax), [Maestro](https://github.com/maestro-project/maestro), and [TVM](https://github.com/apache/tvm) are integrated into HASCO as submodules. Note that we specify Ax and TVM versions for our developing purpose. Other verisons are not tested or guaranteed yet. 
          
1. Clone this repo. 
```
   git clone --recursive https://github.com/pku-liang/HASCO.git HASCO
```
   
2. Install TVM from HASCO/src/tvm. The instructions are given [here](https://tvm.apache.org/docs/install/from_source.html#install-from-source).
3. Compile Maestro from HASCO/src/maestro following these [instructions](http://maestro.ece.gatech.edu/docs/build/html/installation.html). Then, edit the maestro_home [here](https://github.com/pku-liang/HASCO/blob/81180f313ec288403db5061995382c28aff633e2/src/codesign/config.py#L11), if necessary.
4. Intall Ax from HASCO/src/Ax.
```
   python setup.py install
```
   
You can also use docker like [this](https://github.com/pku-liang/HASCO/issues/3#issuecomment-864657367) if you find trouble in the installation. 

## Tests

We have built a number of examples in testbench. To run an example, 
```
   python testbench/co_resnet_conv.py
```
   
You can also build your testcases following our examples. 


## Notices

This version evaluates HASCO-generated solutions with the Maestro tool. We can also use our model [TENET](https://github.com/pku-liang/TENET) in the further vesions. Profiling metrics from hardware prototypes can be supported by integrating our hardware generator [TensorLib](https://github.com/pku-liang/TensorLib). 


## Citing HASCO

If you find HASCO useful for your project, please cite our paper. 
```
@INPROCEEDINGS{xiao2021hasco,
  author={Xiao, Qingcheng and Zheng, Size and Wu, Bingzhe and Xu, Pengcheng and Qian, Xuehai and Liang, Yun},
  booktitle={2021 ACM/IEEE 48th Annual International Symposium on Computer Architecture (ISCA)}, 
  title={HASCO: Towards Agile HArdware and Software CO-design for Tensor Computation}, 
  year={2021},
  volume={},
  number={},
  pages={1055-1068},
  doi={10.1109/ISCA52012.2021.00086}} 
```
You can also find the arxiv version [here](https://arxiv.org/abs/2105.01585). 
