import math

from scipy.integrate import quad


ERROR_CAP = 1. / 1000


def _integrate(f, a, b, args=()):
    result, error = quad(lambda x: f(x * a, *args), 1, b / a)

    if result == 0 or error / result < ERROR_CAP:
        return result * a, error * a

    if b == math.inf:
        split = 2 * a
    else:
        split = (a + b) / 2

    result1, error1 = _integrate(f, a, split, args=args)
    result2, error2 = _integrate(f, split, b, args=args)

    return result1 + result2, error1 + error2


def integrate_piecewise(f, segments, args=()):
    result_accumulator = 0
    error_accumulator = 0
    for x, a, b in segments:
        result, error = _integrate(f, a, b, args=args)
        result_accumulator += x * result
        error_accumulator += error

    return result_accumulator, error_accumulator


def integrate(f, a, b, args=()):
    return _integrate(f, a, b, args=args)
