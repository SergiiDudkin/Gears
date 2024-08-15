import numpy as np
import pytest
from assertpy import assert_that
from assertpy import soft_assertions

from src.gears import seedrange


@pytest.mark.parametrize(
    'st, en, seed, step', [
        [23.5, 79.1, 53.4, 3],
        [23.5, 79.1, 53.4, 4.7],
        [-23.4, 67.5, 54.7, 2.875]
    ]
)
def test_seedrange(st: float, en: float, seed: float, step: float) -> None:
    res = seedrange(st, en, seed, step)
    with soft_assertions():
        tolerance = seed * 1e-5
        assert_that(res[0], 'The first value is out of bounds').is_greater_than_or_equal_to(st)
        assert_that(res[-1], 'The last value is out of bounds').is_less_than_or_equal_to(en)
        assert_that(res[0] - st, 'The first value is skipped').is_less_than(seed * (1 + tolerance))
        assert_that(en - res[-1], 'The last value is skipped').is_less_than(seed * (1 + tolerance))
        if st <= seed <= en:
            assert_that(res[np.argmin(np.abs(res - seed))], 'The seed value not found').is_close_to(seed, tolerance)
