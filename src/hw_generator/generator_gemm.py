import tvm
from hw_generator.generator import generator, accelerator, parse_params

from hw_generator.intrinsic_lib import gemm_intrinsic
from codesign.config import verbose, bits_map


def gemm_interface(f_m, f_n, f_k, l_m, l_n, l_k, c_m, c_n, c_k, d_m, d_n, d_k, dtype):
    """
    l_m, l_n, l_k: last iteration size
    c_m, c_n, c_k: last iteration condition
    """

    _, tensors = gemm_intrinsic(f_m, f_n, f_k, dtype)
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
    strideC = tvm.var("strideC")
    sC = tvm.decl_buffer(tC.shape, tC.dtype,
                        name="sC",
                        offset_factor=1,
                        strides=[strideC, 1])

    iter_m = f_m // d_m + (0 if f_m % d_m == 0 else 1)
    iter_n = f_n // d_n + (0 if f_n % d_n == 0 else 1)
    iter_k = f_k // d_k + (0 if f_k % d_k == 0 else 1)
    pad_m = 0 if f_m % d_m == 0 else (d_m - f_m % d_m)
    pad_n = 0 if f_n % d_n == 0 else (d_n - f_n % d_n)
    pad_k = 0 if f_k % d_k == 0 else (d_k - f_k % d_k)

    last_iter_m = l_m // d_m + (0 if l_m % d_m == 0 else 1)
    last_iter_n = l_n // d_n + (0 if l_n % d_n == 0 else 1)
    last_iter_k = l_k // d_k + (0 if l_k % d_k == 0 else 1)
    last_pad_m = 0 if l_m % d_m == 0 else (d_m - l_m % d_m)
    last_pad_n = 0 if l_n % d_n == 0 else (d_n - l_n % d_n)
    last_pad_k = 0 if l_k % d_k == 0 else (d_k - l_k % d_k)

    iter_m = tvm.if_then_else(c_m, last_iter_m, iter_m)
    iter_n = tvm.if_then_else(c_n, last_iter_n, iter_n)
    iter_k = tvm.if_then_else(c_k, last_iter_k, iter_k)
    pad_m = tvm.if_then_else(c_m, last_pad_m, pad_m)
    pad_n = tvm.if_then_else(c_n, last_pad_n, pad_n)
    pad_k = tvm.if_then_else(c_k, last_pad_k, pad_k)

    # reset-update-finalize
    def interface_func(ins, outs): 
        sa, sb = ins
        sc, = outs

        def _body():
            ib = tvm.ir_builder.create()
            # int32_t matmul_kernel(const elem_t *A, const elem_t *B, 
            #          elem_t *C, const acc_t *D, int32_t I, int32_t J, int32_t K, int32_t pad_I,
            #          int32_t pad_J, int32_t pad_K, int32_t A_row_len,
            #          int32_t B_row_len,  int32_t C_row_len, int32_t D_row_len,
            #          bool no_bias, bool repeating_bias);
            # D is set to a dummy address 1 to determine whether to overwrite
            # accumulator contents: on the first run, 1 will be retained and
            # overwrite the value in the accumulator; on subsequent runs D will be
            # replaced by NULL and C will accumulate on top of the accumulator's contents
            # This is controlled via bit 1 << (ADDR_LEN - 2) - see kernel source
            ib.emit(tvm.call_extern(dtype, "tensorized_GEMM",  
                                    sa.access_ptr("r"),
                                    sb.access_ptr("r"),
                                    sc.access_ptr("rw"),
                                    1,
                                    iter_m, iter_n, iter_k,
                                    pad_m, pad_n, pad_k,
                                    strideA, strideB, strideC, 0,
                                    True, False))
            return ib.get()

        def _reset():
            ib = tvm.ir_builder.create()
            # int32_t matmul_reset(elem_t *C, int32_t I, int32_t J, int32_t pad_I,
            #         int32_t pad_J, int32_t C_row_len);
            ib.emit(tvm.call_extern(dtype, "init_output",
                                    sc.access_ptr("w"),
                                    iter_m, iter_n,
                                    pad_m, pad_n,
                                    strideC))
            return ib.get()

        def _finalize():
            ib = tvm.ir_builder.create()
            # Move out C from accumulator
            # int32_t matmul_finalize(elem_t *C, int32_t I, int32_t J, int32_t pad_I,
            #         int32_t pad_J, int32_t C_row_len);
            ib.emit(tvm.call_extern(dtype, "store_output",
                                    sc.access_ptr("rw"),
                                    iter_m, iter_n,
                                    pad_m, pad_n,
                                    strideC))
            return ib.get()

        # standalone (without reduce axis split), reset, update
        return None, _reset(), _body(), _finalize()


    with tvm.build_config(offset_factor=1):
        return tvm.decl_tensor_intrin(tC.op, interface_func, binds={tA: sA, tB: sB, tC: sC}, name="gemm_interface")




def generate_gemm_interface(M, N, K, fM, fN, fK, axisM, axisN, axisK, dM, dN, dK, sp_kb, local_kb, dtype):
    
    """
    M, N, K: the dimensions mapped to i, j, k
    fM, fN, fK: interface size (fM, fK) * (fK, fN)
    axisM, axisN, axisK: AST nodes 
    dM, dN, dK: intrinsic size
    """

    if verbose:
        assert (fM * fK + fK * fN + fM * fK) <= sp_kb * 8192 / bits_map[dtype], 'data too large for scratchpad'  
        assert (dM * dK + dK * dN + dM * dK) <= local_kb * 8192 / bits_map[dtype], 'data too large for local memory' 
    else:
        assert (fM * fK + fK * fN + fM * fK) <= sp_kb * 8192 / bits_map[dtype] 
        assert (dM * dK + dK * dN + dM * dK) <= local_kb * 8192 / bits_map[dtype]


    last_m = M % fM
    cond_m = tvm.expr.EQ(axisM, M // fM) if last_m != 0 else False # m condition statement
    last_m = last_m if last_m != 0 else fM

    last_n = N % fN   # the last iteration of N
    cond_n = tvm.expr.EQ(axisN, N // fN) if last_n != 0 else False  # n condition statement
    last_n = last_n if last_n != 0 else fN

    last_k = K % fK
    cond_k = tvm.expr.EQ(axisK, K // fK) if last_k != 0 else False  # k condition statement
    last_k = last_k if last_k != 0 else fK

    return gemm_interface(fM, fN, fK, last_m,
                last_n, last_k, cond_m, cond_n, cond_k, dM, dN, dK, dtype)




class GEMMGenerator(generator):
# generate accelerators with GEMM intrinsics 

    def __init__(self, dtype="int8"):
        super().__init__("GEMM", gemm_intrinsic, generate_gemm_interface, dtype)


    def instantiate(self, params, tag): 

        x, y, sp_kb, sp_banks, dma_width, dma_bytes, local_kb, dataflow, dtype = parse_params(self.type, params)

        def acc_interface(M, N, K, fM, fN, fK, axisM, axisN, axisK):
            return self.intf_func(M, N, K, fM, fN, fK, axisM, axisN, axisK, x, y, 1, sp_kb, local_kb, dtype) 

        # 0, 0, 0 placeholder  the i j k dimensions of  mapped GEMMs 
        acc = accelerator(self, acc_interface, params, tag, (0, 0, 0, dtype)) 
        return acc













