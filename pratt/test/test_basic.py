import pytest
from pratt.basic import parse


def test_basic():
    assert(parse("1") == 1)
    assert(parse("1+2+3") == 6)
    assert(parse("1+2*3*4+5") == 30)
    assert(parse("1*2*3") == 6)
