import tvm
from hw_generator.generator import generator, accelerator, parse_params

from hw_generator.intrinsic_lib import conv_intrinsic, gemm_intrinsic

# from flextensor.intrinsic import INTRIN_TABLE
# from inspect import signature
from codesign.config import verbose, bits_map



def conv_interface(f_n, f_c, f_y, f_x, f_k, f_r, f_s,
                   l_n, l_c, l_y, l_x, l_k, l_r, l_s,
                   c_n, c_c, c_y, c_x, c_k, c_r, c_s,
                   d_n, d_c, d_y, d_x, d_k, d_r, d_s, dtype):
    """
    l_n, l_c, l_y, l_x, l_k, l_r, l_s: last iteration size
    c_n, c_c, c_y, c_x, c_k, c_r, c_s: last iteration conditif_son
    """

    _, tensors = conv_intrinsic(f_n, f_c, f_y, f_x, f_k, f_r, f_s, dtype)
    tA, tB, tC = tensors

    # print(tA.shape, tB.shape, tC.shape)
    strideA1 = tvm.var("strideA1")
    strideA2 = tvm.var("strideA2")  
    strideA3 = tvm.var("strideA3")   
    sA = tvm.decl_buffer(tA.shape, tA.dtype,
                        name="sA",
                        offset_factor=1,
                        strides=[strideA1, strideA2, strideA3, 1])
    strideB1 = tvm.var("strideB1")
    strideB2 = tvm.var("strideB2")
    strideB3 = tvm.var("strideB3")
    sB = tvm.decl_buffer(tB.shape, tB.dtype,
                        name="sB",
                        offset_factor=1,
                        strides=[strideB1, strideB2, strideB3, 1])
    strideC1 = tvm.var("strideC1")
    strideC2 = tvm.var("strideC2")
    strideC3 = tvm.var("strideC3")
    sC = tvm.decl_buffer(tC.shape, tC.dtype,
                        name="sC",
                        offset_factor=1,
                        strides=[strideC1, strideC2, strideC3, 1])


    iter_n = f_n // d_n + (0 if f_n % d_n == 0 else 1)
    iter_c = f_c // d_c + (0 if f_c % d_c == 0 else 1)
    iter_y = f_y // d_y + (0 if f_y % d_y == 0 else 1)
    iter_x = f_x // d_x + (0 if f_x % d_x == 0 else 1)
    iter_k = f_k // d_k + (0 if f_k % d_k == 0 else 1)
    iter_r = f_r // d_r + (0 if f_r % d_r == 0 else 1)
    iter_s = f_s // d_s + (0 if f_s % d_s == 0 else 1)


    pad_n = 0 if f_n % d_n == 0 else (d_n - f_n % d_n)
    pad_c = 0 if f_c % d_c == 0 else (d_c - f_c % d_c)
    pad_y = 0 if f_y % d_y == 0 else (d_y - f_y % d_y)
    pad_x = 0 if f_x % d_x == 0 else (d_x - f_x % d_x)
    pad_k = 0 if f_k % d_k == 0 else (d_k - f_k % d_k)
    pad_r = 0 if f_r % d_r == 0 else (d_r - f_r % d_r)
    pad_s = 0 if f_s % d_s == 0 else (d_s - f_s % d_s)

    last_iter_n = l_n // d_n + (0 if l_n % d_n == 0 else 1)
    last_iter_c = l_c // d_c + (0 if l_c % d_c == 0 else 1)
    last_iter_y = l_y // d_y + (0 if l_y % d_y == 0 else 1)
    last_iter_x = l_x // d_x + (0 if l_x % d_x == 0 else 1)
    last_iter_k = l_k // d_k + (0 if l_k % d_k == 0 else 1)
    last_iter_r = l_r // d_r + (0 if l_r % d_r == 0 else 1)
    last_iter_s = l_s // d_s + (0 if l_s % d_s == 0 else 1)


    last_pad_n = 0 if l_n % d_n == 0 else (d_n - l_n % d_n)
    last_pad_c = 0 if l_c % d_c == 0 else (d_c - l_c % d_c)
    last_pad_y = 0 if l_y % d_y == 0 else (d_y - l_y % d_y)
    last_pad_x = 0 if l_x % d_x == 0 else (d_x - l_x % d_x)
    last_pad_k = 0 if l_k % d_k == 0 else (d_k - l_k % d_k)
    last_pad_r = 0 if l_r % d_r == 0 else (d_r - l_r % d_r)
    last_pad_s = 0 if l_s % d_s == 0 else (d_s - l_s % d_s)

    
    iter_n = tvm.if_then_else(c_n, last_iter_n, iter_n)
    iter_c = tvm.if_then_else(c_c, last_iter_c, iter_c)
    iter_y = tvm.if_then_else(c_y, last_iter_y, iter_y)
    iter_x = tvm.if_then_else(c_x, last_iter_x, iter_x)
    iter_k = tvm.if_then_else(c_k, last_iter_k, iter_k)
    iter_r = tvm.if_then_else(c_r, last_iter_r, iter_r)
    iter_s = tvm.if_then_else(c_s, last_iter_s, iter_s)

    pad_n = tvm.if_then_else(c_n, last_pad_n, pad_n)
    pad_c = tvm.if_then_else(c_c, last_pad_c, pad_c)
    pad_y = tvm.if_then_else(c_y, last_pad_y, pad_y)
    pad_x = tvm.if_then_else(c_x, last_pad_x, pad_x)
    pad_k = tvm.if_then_else(c_k, last_pad_k, pad_k)
    pad_r = tvm.if_then_else(c_r, last_pad_r, pad_r)
    pad_s = tvm.if_then_else(c_s, last_pad_s, pad_s)

# reset-update-finalize
    def interface_func(ins, outs): 
        sa, sb = ins
        sc, = outs

        def _body():
            ib = tvm.ir_builder.create()

            ib.emit(tvm.call_extern(dtype, "tensorized_CONV",   
                                    sa.access_ptr("r"),
                                    sb.access_ptr("r"),
                                    sc.access_ptr("rw"),
                                    1,
                                    iter_n, iter_c, iter_y, iter_x, iter_k, iter_r, iter_s,
                                    pad_n, pad_c, pad_y, pad_x, pad_k, pad_r, pad_s, 
                                    True, False))
            return ib.get()

        def _reset():
            ib = tvm.ir_builder.create()

            ib.emit(tvm.call_extern(dtype, "init_output",
                                    sc.access_ptr("w"),
                                    iter_n, iter_y, iter_x, iter_k,
                                    pad_n, pad_y, pad_x, pad_k))
            return ib.get()

        def _finalize():
            ib = tvm.ir_builder.create()

            ib.emit(tvm.call_extern(dtype, "store_output",
                                    sc.access_ptr("rw"),
                                    iter_n, iter_y, iter_x, iter_k,
                                    pad_n, pad_y, pad_x, pad_k))
            return ib.get()

        return None, _reset(), _body(), _finalize()


    with tvm.build_config(offset_factor=1):
        return tvm.decl_tensor_intrin(tC.op, interface_func, binds={tA: sA, tB: sB, tC: sC}, name="conv_interface")



def generate_conv_interface(N, C, Y, X, K, R, S, fN, fC, fY, fX, fK, fR, fS, 
                             axisN, axisC, axisY, axisX, axisK, axisR, axisS, 
                             dN, dC, dY, dX, dK, dR, dS, sp_kb, local_kb, dtype):
    """
    N, C, Y, X, K, R, S: the dimensions mapped to  n, c, y, x, k, r, s
    fN, fC, fY, fX, fK, fR, fS: interface size (fN, fC, fY + fR, fX + fS) * (fR, fS, fC, fK)
    axisN, axisC, axisY, axisX, axisK, axisR, axisS: AST nodes 
    dN, dC, dY, dX, dK, dR, dS: intrinsic size
    """

    if verbose:
        assert fN * fX * fY * fC + fK * fC * fR * fS <= sp_kb * 8192 / bits_map[dtype], 'data too large for scratchpad'  
        assert dN * dX * dY * dC + dK * dC * dR * dS <= local_kb * 8192 / bits_map[dtype], 'data too large for local memory'  
    else:
        assert fN * fX * fY * fC + fK * fC * fR * fS <= sp_kb * 8192 / bits_map[dtype] 
        assert dN * dX * dY * dC + dK * dC * dR * dS <= local_kb * 8192 / bits_map[dtype]
    


    last_n = N % fN   # the last iteration of N
    cond_n = tvm.expr.EQ(axisN, N // fN) if last_n != 0 else False  # n condition statement
    last_n = last_n if last_n != 0 else fN

    last_c = C % fC    
    cond_c = tvm.expr.EQ(axisC, C // fC) if last_c != 0 else False   
    last_c = last_c if last_c != 0 else fC

    last_y = Y % fY   
    cond_y = tvm.expr.EQ(axisY, Y // fY) if last_y != 0 else False   
    last_y = last_y if last_y != 0 else fY

    last_x = X % fX   
    cond_x = tvm.expr.EQ(axisX, X // fX) if last_x != 0 else False  
    last_x = last_x if last_x != 0 else fX

    last_k = K % fK
    cond_k = tvm.expr.EQ(axisK, K // fK) if last_k != 0 else False   
    last_k = last_k if last_k != 0 else fK

    last_r = R % fR
    cond_r = tvm.expr.EQ(axisR, R // fR) if last_r != 0 else False   
    last_r = last_r if last_r != 0 else fR

    last_s = S % fS
    cond_s = tvm.expr.EQ(axisS, S // fS) if last_s != 0 else False   
    last_s = last_s if last_s != 0 else fS

    return conv_interface(fN, fC, fY, fX, fK, fR, fS, last_n, last_c, last_y, last_x, last_k, last_r, last_s,
                        cond_n, cond_c, cond_y, cond_x, cond_k, cond_r, cond_s, dN, dC, dY, dX, dK, dR, dS, dtype)



class CONVGenerator(generator):
# generate accelerators with CONV intrinsics 

    def __init__(self, dtype="int8"):
        super().__init__("CONV", conv_intrinsic, generate_conv_interface, dtype)



    def instantiate(self, params, tag): 

        x, y, sp_kb, sp_banks, dma_width, dma_bytes, local_kb, dataflow, dtype = parse_params(self.type, params)

        def interface_3x3(N, C, Y, X, K, R, S, fN, fC, fY, fX, fK, fR, fS,
                         axisN, axisC, axisY, axisX, axisK, axisR, axisS):
            return self.intf_func(N, C, Y, X, K, R, S, fN, fC, fY, fX, fK, fR, fS,
                                  axisN, axisC, axisY, axisX, axisK, axisR, axisS,
                                  1, y, 16, 16, x, 3, 3, sp_kb, local_kb, dtype)  # intrinsic size is hardware-specific

        # 0s placeholder  the  dimensions of  mapped CONVs 
        acc = accelerator(self, interface_3x3, params, tag, (0, 0, 0, 0, 0, 0, 0, dtype)) 


        # def interface_1x1(N, C, Y, X, K, R, S, fN, fC, fY, fX, fK, fR, fS,
        #                  axisN, axisC, axisY, axisX, axisK, axisR, axisS):
        #     from hw_generator.generator_gemm import generate_gemm_interface
        #     return generate_gemm_interface(K, Y, C, fK, fY, fC, axisK, axisY, axisC, x, y, 1, sp_kb, local_kb, dtype) 

        # acc.add_intrinsic(gemm_intrinsic, (0, 0, 0, dtype), interface_1x1)

        return acc













