import pytest
from pratt.full import parse


def test_full():
    assert(parse("1") == 1)
    assert(parse("-1") == -1)
    assert(parse("0+1+2*3*-4+5**2!") == 2)
    assert(parse("---1++2+~1") == 2)
    assert(parse("1*(2+ (-3-1))") == -2)
    assert(parse("2**2**3") == 256)
