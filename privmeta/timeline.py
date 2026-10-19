import random
from datetime import timedelta


def random_between(start, end):
    if end < start:
        raise ValueError("end must not be earlier than start")
    span = (end - start).total_seconds()
    offset = random.uniform(0.0, span)
    return start + timedelta(seconds=offset)


def sequential(start, end, count):
    if count <= 0:
        return []
    if count == 1:
        return [start]
    if end < start:
        raise ValueError("end must not be earlier than start")
    step = (end - start) / (count - 1)
    return [start + step * index for index in range(count)]