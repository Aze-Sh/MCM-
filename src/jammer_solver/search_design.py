"""Search layout helper; Q4 uses the certified 21 points in solver.py."""
import math


def design(problem):
    if problem == 3:
        return [(0.,0.)]+[(1125*math.cos(k*math.pi/3),1125*math.sin(k*math.pi/3)) for k in range(6)]
    if problem != 4:
        raise ValueError("problem must be 3 or 4")
    inner=[(990*math.cos(k*math.pi/4),990*math.sin(k*math.pi/4)) for k in range(8)]
    outer=[(1836*math.cos(k*math.pi/8),1836*math.sin(k*math.pi/8)) for k in range(16)]
    return [(0.,0.)]+inner+[outer[(14+k)%16] for k in range(16)]
