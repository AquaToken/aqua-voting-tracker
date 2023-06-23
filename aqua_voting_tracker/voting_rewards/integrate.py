import math

from scipy.integrate import quad


ERROR_CAP = 1. / 10 ** 6
SPLIT_LIMIT = 1000


class SplitOverLimitError(Exception):
    message = 'The partitioning process has reached its limit.'


class IntegratePartition:
    __slots__ = ('a', 'b', 'result', 'error')

    def __init__(self, f, a, b, args=()):
        self.a = a
        self.b = b
        self.result, self.error = quad(f, self.a, self.b, args=args)

    def __repr__(self):
        return f'{self.a}-{self.b}: {self.result}, {self.error}'

    def split(self, f, args=()):
        if self.b == math.inf:
            split_point = self.a * 2
        else:
            split_point = (self.a + self.b) / 2

        return (
            IntegratePartition(f, self.a, split_point, args=args),
            IntegratePartition(f, split_point, self.b, args=args),
        )


def _integrate(f, a, b, args=()):
    assert 0. < a <= b, "The partitioning flow cannot work with negative borders."

    if a == b:
        return 0., 0.

    partition_list = [
        IntegratePartition(f, a, b, args=args),
    ]
    while True:
        result_sum = sum(part.result for part in partition_list)
        new_partition_list = []

        for part in partition_list:
            if part.error / result_sum > ERROR_CAP:
                new_partition_list.extend(part.split(f, args=args))
            else:
                new_partition_list.append(part)

        if len(partition_list) == len(new_partition_list):
            return result_sum, sum(part.error for part in partition_list)
        else:
            partition_list = new_partition_list

        if len(partition_list) > SPLIT_LIMIT:
            raise SplitOverLimitError()


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
