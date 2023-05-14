from cpos.core.sortition import binomial, cumulative_binom_dist
import pytest

def test_binomial():
    assert binomial(1, 0) == 1
    assert binomial(1, 1) == 1
    assert binomial(123, 1) == 123
    assert binomial(6, 3) == 20
    with pytest.raises(ValueError) as _:
        binomial(5, 6)

def test_cumulative_binom_dist():
    error = abs(cumulative_binom_dist(120, 120, 0.1) - 1.0)
    assert error < 1e-8
