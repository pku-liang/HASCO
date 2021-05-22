#done
import tvm
import math

CONST = 1 # constant placeholder for matching purpose

# code generation for convoltutions with stride > 1 is a known issue
def conv2d_compute(N, C, Y, X, K, R, S, stride=1, dtype="int8", layout="GEMM", padding=False):  # padding == SAME
    y_padding = (R - 1) / 2 if padding else 0  
    x_padding = (S - 1) / 2 if padding else 0 
    Yo = math.floor((Y + 2 * y_padding - R) / stride) + 1 
    Xo = math.floor((X + 2 * x_padding - S) / stride) + 1
    # Y = Yo * stride
    # X = Xo * stride
    '''
    should be simple as:
        Input = tvm.placeholder((N, Y, X, C), name="A", dtype=dtype)
        Filter = tvm.placeholder((R, S, C, K), name="B", dtype=dtype)
        r = tvm.reduce_axis((0, R), name="r")
        s = tvm.reduce_axis((0, S), name="s")
        c = tvm.reduce_axis((0, C), name="c")
        Output = tvm.compute(
            (N, Yo, Xo, K),
            lambda n, y, x, k: tvm.sum(
                Input[n, stride * y + r, stride * x + s, c] * Filter[r, s, c, k],
                axis=[r, s, c]
            ), name="C")
    but we use some tricks (stride and layout) for matching purpose. This can be improved. 
    '''
    # R = R if R > 1 else CONST  # for matching purpose
    # S = S if S > 1 else CONST
    # C = C if C > 1 else CONST

    if layout in ["GEMM", "CONV"]:
        Input = tvm.placeholder((N, Y, X, C), name="A", dtype=dtype)
        Filter = tvm.placeholder((R, S, C, K), name="B", dtype=dtype)

        r = tvm.reduce_axis((0, R), name="r")
        s = tvm.reduce_axis((0, S), name="s")
        c = tvm.reduce_axis((0, C), name="c") 

        Output = tvm.compute(
            (N, Yo, Xo, K),
            lambda n, y, x, k: tvm.sum(
                Input[n, y + r, x + s, c] * Filter[r, s, c, k],
                axis=[r, s, c]
            ), name="C")
    elif layout == "GEMV":
        Input = tvm.placeholder((N, Y, X, C), name="A", dtype=dtype)
        Filter = tvm.placeholder((R, S, K, C), name="B", dtype=dtype)
        r = tvm.reduce_axis((0, R), name="r")
        s = tvm.reduce_axis((0, S), name="s")
        c = tvm.reduce_axis((0, C), name="c")
        Output = tvm.compute(
            (N, Yo, Xo, K),
            lambda n, y, x, k: tvm.sum(
                Input[n, y + r, x + s, c] * Filter[r, s, k, c],
                axis=[r, s, c]
            ), name="C")
    else:
        Input = tvm.placeholder(( N, Y, X, CONST, C), name="A", dtype=dtype)
        Filter = tvm.placeholder((R, S, K, CONST, C), name="B", dtype=dtype)
        r = tvm.reduce_axis((0, R), name="r")
        s = tvm.reduce_axis((0, S), name="s")
        c = tvm.reduce_axis((0, C), name="c")
        Output = tvm.compute(
            (N, Yo, Xo, CONST, K),
            lambda n, y, x, e, k: tvm.sum(
                Input[n, y + r, x + s, e, c] * Filter[r, s, k, e, c],
                axis=[r, s, c]
            ), name="C")   


    return [Output.op], [Input, Filter, Output]



def dwconv_compute(N, C, Y, X, K, R, S, stride=1, dtype="int8", layout="GEMM", padding=False):
    y_padding = (R - 1) / 2 if padding else 0  
    x_padding = (S - 1) / 2 if padding else 0 
    Yo = math.floor((Y + 2 * y_padding - R) / stride) + 1 
    Xo = math.floor((X + 2 * x_padding - S) / stride) + 1
    Ko = C * K
    '''
    should be simple as:
        Input = tvm.placeholder((N, Y, X, C), name="A", dtype=dtype)
        Filter = tvm.placeholder((R, S, K, C), name="B", dtype=dtype)
        r = tvm.reduce_axis((0, R), name="r")
        s = tvm.reduce_axis((0, S), name="s")
        Output = tvm.compute(
            (N, Yo, Xo, Ko),
            lambda n, y, x, k: tvm.sum(
                Input[n, stride * y + r, stride * x + s, c] * Filter[r, s, k / C, k % C],
                axis=[r, s]
            ), name="C")
    
    We use some tricks (stride and layout) to match the conv intrinsic. 
    In practice, our CONV accelerator supports dwconv intrinsic.
    We can address the matching problem by adding a dwconv intrinsic to the accelerator. 
    '''
    Input = tvm.placeholder((N, Y, X, C), name="A", dtype=dtype)
    Filter = tvm.placeholder((R, S, K, C), name="B", dtype=dtype)
    r = tvm.reduce_axis((0, R), name="r")
    s = tvm.reduce_axis((0, S), name="s")
    c = tvm.reduce_axis((0, C), name="c")
    Output = tvm.compute(
        (N, Yo, Xo, Ko),
        lambda n, y, x, k: tvm.sum(
            Input[n, y + r, x + s, c] * Filter[r, s, c, k],
            axis=[r, s, c]
        ), name="C")
    return [Output.op], [Input, Filter, Output]




def mm_compute(M, N, K, dtype="int8", layout="GEMM"):

    if layout == "GEMM":
        A = tvm.placeholder((M, K), name='A', dtype=dtype)
        B = tvm.placeholder((K, N), name='B', dtype=dtype)
        kk = tvm.reduce_axis((0, K), 'c')
        C = tvm.compute(
            (M, N),
            lambda k, y: tvm.sum(A[k, kk] * B[kk, y], axis=kk),
            name='C')

    elif layout == "GEMV":
        A = tvm.placeholder((M, K), name='A', dtype=dtype)
        B = tvm.placeholder((N, K), name='B', dtype=dtype)
        kk = tvm.reduce_axis((0, K), 'c')
        C = tvm.compute(
            (M, N),
            lambda k, y: tvm.sum(A[k, kk] * B[y, kk], axis=kk),
            name='C')

    elif layout == "CONV":
        A = tvm.placeholder((CONST, N, CONST, K), name='A', dtype=dtype)
        B = tvm.placeholder((CONST, CONST, K, M), name='B', dtype=dtype)
        kk = tvm.reduce_axis((0, K), 'c')
        r = tvm.reduce_axis((0, CONST), 'r')
        s = tvm.reduce_axis((0, CONST), 's') 
        C = tvm.compute(
            (CONST, N, CONST, M),
            lambda n, y, x, k: tvm.sum(A[n, y + r, x + s, kk] * B[r, s, kk, k], axis=[r, s, kk]),
            name='C')
    
    else:
        A = tvm.placeholder((M, CONST, K), name='A', dtype=dtype)
        B = tvm.placeholder((N, CONST, K), name='B', dtype=dtype)
        kk = tvm.reduce_axis((0, K), 'c')
        C = tvm.compute(
            (M, CONST, N),
            lambda k, x, y: tvm.sum(A[k, x, kk] * B[y, x, kk], axis=kk),
            name='C')


    return [C.op], [A, B, C]




def gemv_compute(M, N, L, dtype="int8", layout="GEMV"):

    if layout == "GEMV":
        C = tvm.placeholder([N, M, L], name="C", dtype=dtype)
        D = tvm.placeholder([N, L], name="D", dtype=dtype)

        l = tvm.reduce_axis([0, L], name="c")
        E = tvm.compute([M, N],
                        lambda k, y: tvm.sum(C[y, k, l] * D[y, l], axis=[l]),
                        name="E")
        return [E.op], [C, D, E]

    elif layout == "DOT":
        C = tvm.placeholder([M, N, L], name="C", dtype=dtype)
        D = tvm.placeholder([N, L], name="D", dtype=dtype)
        
        l = tvm.reduce_axis([0, L], name="c")
        E = tvm.compute([M, N],
                        lambda k, y: tvm.sum(C[k, y, l] * D[y, l], axis=[l]),
                        name="E")

        return [E.op], [C, D, E]

    else:
        print("Unsupported layout yet...")




def ttm_compute(M, N, K, L, dtype="int8", layout="GEMM"):
    if layout == "GEMM":
        A = tvm.placeholder([M, N, L], name="A", dtype=dtype)
        B = tvm.placeholder([L, K], name="B", dtype=dtype)
        l = tvm.reduce_axis([0, L], name="c")
        C = tvm.compute([M, N, K],
                        lambda y, x, k: tvm.sum(A[y, x, l] * B[l, k], axis=[l]),
                        name="C")
    
    elif layout == "GEMV":
        A = tvm.placeholder([M, N, L], name="A", dtype=dtype)
        B = tvm.placeholder([K, L], name="B", dtype=dtype)
        l = tvm.reduce_axis([0, L], name="c")
        C = tvm.compute([M, N, K],
                        lambda y, x, k: tvm.sum(A[y, x, l] * B[k, l], axis=[l]),
                        name="C")

    else:
        A = tvm.placeholder([M, N, CONST, L], name="A", dtype=dtype)
        B = tvm.placeholder([K, CONST, L], name="B", dtype=dtype)
        l = tvm.reduce_axis([0, L], name="c")
        e = tvm.reduce_axis([0, CONST], name="e")
        C = tvm.compute([M, N, CONST, K],
                        lambda y, x, e, k: tvm.sum(A[y, x, e, l] * B[k, e, l], axis=[l]),
                        name="C")

    return [C.op], [A, B, C]




def mttkrp_compute(M, N, K, L, dtype="int8", layout="GEMM", stage=0):  # can be automated

    if layout in ["GEMV", "DOT"]:
        if stage == 1:  # ttm stage 
            return ttm_compute(M, L, N, K, dtype, layout)
        elif stage == 2:  # gemv stage
            return gemv_compute(M, N, L, dtype, layout)
        else:
            pass
    else:  # tensor computations with multiple input tensors can be improved
        A = tvm.placeholder([M, K, L], name="A", dtype=dtype)
        B = tvm.placeholder([N, K], name="B", dtype=dtype)
        C = tvm.placeholder([N, L], name="C", dtype=dtype)

        k = tvm.reduce_axis([0, K], name="k")
        l = tvm.reduce_axis([0, L], name="l")
        D = tvm.compute([M, N], 
                        lambda m, n: tvm.sum(A[m, k, l] * B[n, k] * C[n, l], axis=[k, l]),
                        name="D")
        return [D.op], [A, B, C, D]
