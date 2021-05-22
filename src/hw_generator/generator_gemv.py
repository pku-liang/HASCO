import tvm
from hw_generator.generator import generator, accelerator, parse_params

from hw_generator.intrinsic_lib import gemv_intrinsic
from codesign.config import verbose, bits_map


def gemv_interface(f_m, f_n, l_m, l_n, c_m, c_n, d_m, d_n, dtype):
    """
    l_m, l_n: last iteration size
    c_m, c_n: last iteration condition
    """

    _, tensors = gemv_intrinsic(f_m, f_n, dtype)
    tA, tB, tC = tensors

    strideA = tvm.var("strideA")  
    sA = tvm.decl_buffer(tA.shape, tA.dtype,
                        name="sA",
                        offset_factor=1,
                        strides=[strideA, 1]) 
    sB = tvm.decl_buffer(tB.shape, tB.dtype,
                        name="sB",
                        offset_factor=1,
                        strides=[1]) 
    sC = tvm.decl_buffer(tC.shape, tC.dtype,
                        name="sC",
                        offset_factor=1,
                        strides=[1])

    iter_m = f_m // d_m + (0 if f_m % d_m == 0 else 1)
    iter_n = f_n // d_n + (0 if f_n % d_n == 0 else 1)
    pad_m = 0 if f_m % d_m == 0 else (d_m - f_m % d_m)
    pad_n = 0 if f_n % d_n == 0 else (d_n - f_n % d_n)

    last_iter_m = l_m // d_m + (0 if l_m % d_m == 0 else 1)
    last_iter_n = l_n // d_n + (0 if l_n % d_n == 0 else 1)
    last_pad_m = 0 if l_m % d_m == 0 else (d_m - l_m % d_m)
    last_pad_n = 0 if l_n % d_n == 0 else (d_n - l_n % d_n)

    iter_m = tvm.if_then_else(c_m, last_iter_m, iter_m)
    iter_n = tvm.if_then_else(c_n, last_iter_n, iter_n)
    pad_m = tvm.if_then_else(c_m, last_pad_m, pad_m)
    pad_n = tvm.if_then_else(c_n, last_pad_n, pad_n)

    # reset-update-finalize
    def interface_func(ins, outs): 
        sa, sb = ins
        sc, = outs
        # print(sa.strides, sb.strides, sc.strides)

        def _body():
            ib = tvm.ir_builder.create()
            ib.emit(tvm.call_extern(dtype, "tensorized_GEMV",   
                                    sa.access_ptr("r"),
                                    sb.access_ptr("r"),
                                    sc.access_ptr("rw"),
                                    1,
                                    iter_m, iter_n, 
                                    pad_m, pad_n,
                                    strideA, 1, 1, 0,
                                    True, False))
            return ib.get()

        def _reset():
            ib = tvm.ir_builder.create()
            ib.emit(tvm.call_extern(dtype, "init_output",
                                    sc.access_ptr("w"),
                                    iter_m, pad_m, 
                                    1))
            return ib.get()

        def _finalize():
            ib = tvm.ir_builder.create()
            ib.emit(tvm.call_extern(dtype, "store_output",
                                    sc.access_ptr("rw"),
                                    iter_m, pad_m,
                                    1))
            return ib.get()

        return None, _reset(), _body(), _finalize()

    with tvm.build_config(offset_factor=1):
        return tvm.decl_tensor_intrin(tC.op, interface_func, binds={tA: sA, tB: sB, tC: sC}, name="gemv_interface")


def generate_gemv_interface(M, N, fM, fN, axisM, axisN, dM, dN, sp_kb, local_kb, dtype):
    
    """
    M, N: the dimensions mapped to i, j
    fM, fN: interface size (fM, fN) * (fN)
    axisM, axisN: AST nodes 
    dM, dN: intrinsic size
    """


    if verbose:
        assert (fM * fN + fM + fN) <= sp_kb * 8192 / bits_map[dtype], 'data too large for scratchpad'
        assert (dM * dN + dM + dN) <= local_kb * 8192 / bits_map[dtype], 'data too large for local memory'
    else:
        assert (fM * fN + fM + fN) <= sp_kb * 8192 / bits_map[dtype]
        assert (dM * dN + dM + dN) <= local_kb * 8192 / bits_map[dtype]


    last_m = M % fM
    cond_m = tvm.expr.EQ(axisM, M // fM) if last_m != 0 else False # m condition statement
    last_m = last_m if last_m != 0 else fM

    last_n = N % fN   # the last iteration of N
    cond_n = tvm.expr.EQ(axisN, N // fN) if last_n != 0 else False  # n condition statement
    last_n = last_n if last_n != 0 else fN

    return gemv_interface(fM, fN, last_m, last_n, cond_m, cond_n, dM, dN, dtype)



class GEMVGenerator(generator):
# generate accelerators with GEMV intrinsics 

    def __init__(self, dtype="int8"):
        super().__init__("GEMV", gemv_intrinsic, generate_gemv_interface, dtype)



    def instantiate(self, params, tag): 

        x, y, sp_kb, sp_banks, dma_width, dma_bytes, local_kb, dataflow, dtype = parse_params(self.type, params)

        def acc_interface(M, N, fM, fN, axisM, axisN):
            return self.intf_func(M, N, fM, fN, axisM, axisN, x * y, 1, sp_kb, local_kb, dtype) 

        # 0, 0 placeholder  the i j dimensions of  mapped GEMVs 
        acc = accelerator(self, acc_interface, params, tag, (0, 0, dtype))  
        return acc













