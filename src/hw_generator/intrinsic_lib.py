import tvm

def gemm_intrinsic(i, j, k, dtype):
    a = tvm.placeholder((i, k), name='a', dtype=dtype)
    b = tvm.placeholder((k, j), name='b', dtype=dtype)
    kk = tvm.reduce_axis((0, k), name='k')
    c = tvm.compute((i, j), lambda ii, jj:
                    tvm.sum(a[ii, kk] * b[kk, jj], axis=kk), name='c')

    return c, [a, b, c]


def gemv_intrinsic(i, j, dtype):
    a = tvm.placeholder((i, j), name='a', dtype=dtype)
    b = tvm.placeholder((j, ), name='b', dtype=dtype)
    jj = tvm.reduce_axis((0, j), name='j')
    c = tvm.compute((i, ), lambda ii:
                    tvm.sum(a[ii, jj] * b[jj], axis=jj), name='c')
    
    return c, [a, b, c]



def dot_intrinsic(n, i, dtype):
    a = tvm.placeholder((n, i), name='a', dtype=dtype)
    b = tvm.placeholder((n, i), name='b', dtype=dtype)
    ii = tvm.reduce_axis((0, i), name='i')
    c = tvm.compute( (n,), lambda nn:
                    tvm.sum(a[nn, ii] * b[nn, ii], axis=ii), name='c')

    return c, [a, b, c]



def conv_intrinsic(n, c, y, x, k, r, s, dtype):

    a = tvm.placeholder((n, y + r - 1, x + s - 1, c), name='a', dtype=dtype) # unused size
    b = tvm.placeholder((r, s, c, k), name='b', dtype=dtype)

    rr = tvm.reduce_axis((0, r), name="r")
    ss = tvm.reduce_axis((0, s), name="s")
    cc = tvm.reduce_axis((0, c), name="c")

    o =  tvm.compute((n, y, x, k), lambda nn, yy, xx, kk:
                    tvm.sum(a[nn, yy + rr, xx + ss, cc] * b[rr, ss, cc, kk], axis=[rr, ss, cc]), name='o')

    return o, [a, b, o]
