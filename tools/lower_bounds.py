"""Certified necessary operation cost to rule out each truly absent channel."""
from fractions import Fraction as F
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from jammer_solver.exact_geometry import trig


def per_channel(problem):
    # Outward angle bounds, checked by the rational Taylor kernel. These
    # angular measures may overlap; their SUM must nevertheless reach 360.
    beta = F('1.274')
    assert trig(beta/2)[2]>=F(1,90)
    if problem==3:
        alpha = F('67.499')
        assert trig(alpha/2)[2]>=F(5,9)
    elif problem==4:
        alpha = F('58.110')
        cl,ch,sl,sh = trig(alpha/2)
        assert sl>=F(5,9)*ch and cl>0
    else:
        raise ValueError('Expected problem 3 or 4')
    for cost in range(100):
        if any(m*alpha+k*beta>=360 for m in range(cost//5+1)
               for k in range((cost-5*m)//3+1)):
            return cost
    raise ArithmeticError('Angular lower bound enumeration failed')


def absence_lower(problem,count):
    if not 10<=count<=16:
        raise ValueError('Expected 10–16 sources')
    return 0 if count==16 else (20-count)*per_channel(problem)
