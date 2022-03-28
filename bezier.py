import time

import numpy as np
from matplotlib import pyplot as plt
from numba import float64, jit


@jit(
    float64[:](float64[:], float64[:], float64[:], float64[:]),
    nopython=True,
    nogil=True,
)
def TDMAsolver(a, b, c, d):
    """
    TDMA solver, a b c d can be NumPy array type or Python list type.
    refer to http://en.wikipedia.org/wiki/Tridiagonal_matrix_algorithm
    and to http://www.cfd-online.com/Wiki/Tridiagonal_matrix_algorithm_-_TDMA_(Thomas_algorithm)
    """
    nf = len(d)  # number of equations
    ac, bc, cc, dc = a.copy(), b.copy(), c.copy(), d.copy()
    for it in range(1, nf):
        mc = ac[it - 1] / bc[it - 1]
        bc[it] = bc[it] - mc * cc[it - 1]
        dc[it] = dc[it] - mc * dc[it - 1]

    xc = bc
    xc[-1] = dc[-1] / bc[-1]

    for il in range(nf - 2, -1, -1):
        xc[il] = (dc[il] - cc[il] * xc[il + 1]) / bc[il]

    return xc


def get_bezier_coef(points):
    n = len(points) - 1

    # build coefficents matrix
    a = np.ones((n - 1))
    a[-1] = 2
    b = np.ones((n)) * 4
    b[0] = 2
    b[-1] = 7
    c = np.ones((n - 1))

    # build points vector
    Px = [2 * (2 * points[i][0] + points[i + 1][0]) for i in range(n)]
    Px[0] = points[0][0] + 2 * points[1][0]
    Px[n - 1] = 8 * points[n - 1][0] + points[n][0]
    Px = np.array(Px)
    Py = [2 * (2 * points[i][1] + points[i + 1][1]) for i in range(n)]
    Py[0] = points[0][1] + 2 * points[1][1]
    Py[n - 1] = 8 * points[n - 1][1] + points[n][1]
    Py = np.array(Py)

    # solve system, find a & b
    Ax = TDMAsolver(a, b, c, Px)
    Ay = TDMAsolver(a, b, c, Py)
    A = np.stack([Ax, Ay], axis=-1)
    B = [0] * n
    for i in range(n - 1):
        B[i] = 2 * points[i + 1] - A[i + 1]
    B[n - 1] = (A[n - 1] + points[n]) / 2
    B = np.array(B)

    return A, B


def get_cubic(a, b, c, d):
    return (
        lambda t: np.power(1 - t, 3) * a
        + 3 * np.power(1 - t, 2) * t * b
        + 3 * (1 - t) * np.power(t, 2) * c
        + np.power(t, 3) * d
    )


def get_bezier_cubic(points):
    A, B = get_bezier_coef(points)
    return [
        get_cubic(points[i], A[i], B[i], points[i + 1]) for i in range(len(points) - 1)
    ]


def evaluate_bezier(points, n):
    curves = get_bezier_cubic(points)
    return np.array([fun(t) for fun in curves for t in np.linspace(0, 1, n)])


if __name__ == "__main__":
    points = np.random.rand(5, 2)
    t0 = time.time()
    path = evaluate_bezier(points, 50)
    t1 = time.time()
    print("numba {}".format(t1 - t0))

    x, y = points[:, 0], points[:, 1]
    px, py = path[:, 0], path[:, 1]

    # plot
    plt.figure(figsize=(11, 8))
    plt.plot(px, py, "b-")
    plt.plot(x, y, "ro")
    plt.show()
