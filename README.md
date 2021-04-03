# HASCO

Tensor computation is fundamental for many scientific and engineering applications, such as machine learning, data mining, quantum chemistry. Though dedicated hardware and software optimizations have progressed considerably for tensor computation, they primarily focus on either the hardware part or the software part. Optimizing the two parts in isolation inevitably suffers from sub-optimal solutions confined in a local design space. 

While seemingly appealing, there has been less attention on hardware/software co-design for tensor computation. This is largely because the design of hardware and software components influence each other, and the joint design space can be huge. A general approach to tackle the co-design problem is to develop a unified intermediate representation (IR), based on which designers can partition the hardware and software, optimize, and synthesize the hardware and software. However, developing such a general IR and synthesizing arbitrary hardware are challenging. 

We provide a co-design approach specific to tensor computation —— HASCO. As tensor computation can be described using nested loops, we naturally embed loop information into our IR design for tensor computation partitioning, optimization, and implementation. A subset of the loops are implemented using spatial hardware accelerators, and the remaining loops are implemented using software programs. The fundamental questions are: 1) how to define the interface between the hardware accelerators and the software programs, 2) how to navigate the huge design space for each part.

We propose HASCO to co-design hardware accelerators and software mapping in concert. HASCO offers a holistic solution to tensor computations.
    
We propose efficient algorithms to explore the hardware-software interface (tensorize).
    
We develop heuristic, Q-learning, and Bayesian optimization algorithms to explore the design spaces efficiently. 
    
    
The source code is coming soon.
