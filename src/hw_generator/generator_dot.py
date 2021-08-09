import tvm
from hw_generator.generator import generator, accelerator, parse_params

from hw_generator.intrinsic_lib import dot_intrinsic
from codesign.config import verbose, bits_map



def dot_interface(f_n, f_k, l_n, l_k, c_n, c_k, d_n, d_k, dtype):
    """
    l_n, l_k: last iteration size
    c_n, c_k: last iteration condition
    """

    _, tensors = dot_intrinsic(f_n, f_k, dtype)
    tA, tB, tC = tensors

    strideA = tvm.var("strideA")  
    sA = tvm.decl_buffer(tA.shape, tA.dtype,
                        name="sA",
                        offset_factor=1,
                        strides=[strideA, 1])
    strideB = tvm.var("strideB")
    sB = tvm.decl_buffer(tB.shape, tB.dtype,
                        name="sB",
                        offset_factor=1,
                        strides=[strideB, 1]) 
                        
    sC = tvm.decl_buffer(tC.shape, tC.dtype,
                        name="sC",
                        offset_factor=1,
                        strides=[1])

    iter_n = f_n // d_n + (0 if f_n % d_n == 0 else 1)
    iter_k = f_k // d_k + (0 if f_k % d_k == 0 else 1)

    pad_n = 0 if f_n % d_n == 0 else (d_n - f_n % d_n)
    pad_k = 0 if f_k % d_k == 0 else (d_k - f_k % d_k)

    last_iter_n = l_n // d_n + (0 if l_n % d_n == 0 else 1)
    last_iter_k = l_k // d_k + (0 if l_k % d_k == 0 else 1)
    last_pad_n = 0 if l_n % d_n == 0 else (d_n - l_n % d_n)
    last_pad_k = 0 if l_k % d_k == 0 else (d_k - l_k % d_k)


    iter_n = tvm.if_then_else(c_n, last_iter_n, iter_n)
    iter_k = tvm.if_then_else(c_k, last_iter_k, iter_k)
    pad_n = tvm.if_then_else(c_n, last_pad_n, pad_n)
    pad_k = tvm.if_then_else(c_k, last_pad_k, pad_k)

    # reset-update-finalize
    def interface_func(ins, outs): 
        sa, sb = ins
        sc, = outs

        def _body():
            ib = tvm.ir_builder.create()
            ib.emit(tvm.call_extern(dtype, "tensorized_DOT",   
                                    sa.access_ptr("r"),
                                    sb.access_ptr("r"),
                                    sc.access_ptr("rw"),
                                    1,
                                    iter_n, iter_k, pad_n, pad_k,
                                    strideA, strideB, 1, 0,
                                    True, False))
            return ib.get()

        def _reset():
            ib = tvm.ir_builder.create()
            ib.emit(tvm.call_extern(dtype, "init_output",
                                    sc.access_ptr("w"),
                                    iter_n, iter_k,
                                    pad_n, pad_k, 
                                    1))
            return ib.get()

        def _finalize():
            ib = tvm.ir_builder.create()
            ib.emit(tvm.call_extern(dtype, "store_output",
                                    sc.access_ptr("rw"),
                                    iter_n, iter_k,
                                    pad_n, pad_k, 
                                    1))
            return ib.get()

        return None, _reset(), _body(), _finalize()


    with tvm.build_config(offset_factor=1):
        return tvm.decl_tensor_intrin(tC.op, interface_func, binds={tA: sA, tB: sB, tC: sC}, name="dot_interface")


def generate_dot_interface(N, K, fN, fK, axisN, axisK, dN, dK, sp_kb, local_kb, dtype):
    
    """
    N, K: the dimensions mapped to n, i
    fN, fK: interface size (fN, fK) * (fN, fK)
    axisN, axisK: AST nodes 
    dN, dK: intrinsic size
    """
    
    if verbose:
        assert (2 * fN * fK + fN) <= sp_kb * 8192 / bits_map[dtype], 'data too large for scratchpad'  
        assert (2 * dN * dK + dN) <= local_kb * 8192 / bits_map[dtype], 'data too large for local memory'  
    else:
        assert (2 * fN * fK + fN) <= sp_kb * 8192 / bits_map[dtype]
        assert (2 * dN * dK + dN) <= local_kb * 8192 / bits_map[dtype]
    
    last_n = N % fN   # the last iteration of N
    cond_n = tvm.expr.EQ(axisN, N // fN) if last_n != 0 else False  # n condition statement
    last_n = last_n if last_n != 0 else fN

    last_k = K % fK
    cond_k = tvm.expr.EQ(axisK, K // fK) if last_k != 0 else False  # k condition statement
    last_k = last_k if last_k != 0 else fK

    return dot_interface(fN, fK, last_n, last_k, cond_n, cond_k, dN, dK, dtype)


class DOTGenerator(generator):
# generate accelerators with GEMV intrinsics 

    def __init__(self, dtype="int8"):
        super().__init__("DOT", dot_intrinsic, generate_dot_interface, dtype)


    def instantiate(self, params, tag): 

        x, y, sp_kb, sp_banks, dma_width, dma_bytes, local_kb, dataflow, dtype = parse_params(self.type, params)

        intrin_size = [1, x * y]

        def acc_interface(N, K, fN, fK, axisN, axisK):
            return self.intf_func(N, K, fN, fK, axisN, axisK, *intrin_size, sp_kb, local_kb, dtype)

        # 0, 0 placeholder  the i j dimensions of mapped DOTs 
        acc = accelerator(self, acc_interface, params, tag, (0, 0, dtype)) 
        return acc













