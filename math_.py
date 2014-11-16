from __future__ import division, print_function

from numpy.testing import assert_almost_equal

SCALING_FACTOR = 400

def expected_score(me, other):
    expected_score_ = 1 / (1 + 10**((other - me)/SCALING_FACTOR))
    return expected_score_


def update_rating(rating1, rating2, K1, K2, score1, score2):
    n_rounds = score1 + score2
    expected_score1 = expected_score(rating1, rating2) * n_rounds
    expected_score2 = expected_score(rating2, rating1) * n_rounds
    assert_almost_equal(
        expected_score1 + expected_score2,
        n_rounds
    )
    new_rating1 = rating1 + K1 * (score1 - expected_score1)
    new_rating2 = rating2 + K1 * (score2 - expected_score2)
    return new_rating1, new_rating2


