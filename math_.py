from __future__ import division, print_function

from numpy.testing import assert_almost_equal

SCALING_FACTOR = 400

def expected_score(me, other):
    expected_score_ = 1 / (1 + 10**((other - me)/SCALING_FACTOR))
    return expected_score_


def boX_expected_score(expected_score, X=15):
    winning_no = (X + 1) / 2
    if expected_score > 0.5:
        res = 8 * (1 - expected_score) / expected_score
    else:
        res = 8 * expected_score / (1 - expected_score)
    return res


def update_rating(rating1, rating2, K1, K2, score1, score2):
    n_rounds = score1 + score2
    expected_score1 = expected_score(rating1, rating2)
    expected_score2 = expected_score(rating2, rating1)
    assert_almost_equal(
        expected_score1 + expected_score2,
        1
    )
    rel_score1 = score1 / n_rounds
    rel_score2 = score2 / n_rounds
    new_rating1 = rating1 + K1 * (rel_score1 - expected_score1)
    new_rating2 = rating2 + K2 * (rel_score2 - expected_score2)
    return new_rating1, new_rating2


