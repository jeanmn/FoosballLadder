from __future__ import division, print_function

from itertools import product

from nose.tools import (
    assert_equal,
    assert_almost_equal
)


class test_expected_score(object):
    def test_even(self):
        from math_ import expected_score
        me = 1500
        other = 1500
        es = expected_score(me, other)
        assert_equal(es, 0.5)

    def test_sums_to_one(self):
        from math_ import expected_score
        mes = [90, 120, 142, 1592, 1593, 12381]
        others = [11, 23, 1239, 10100]
        for (me, other) in product(mes, others):
            es1, es2 = map(expected_score, [me, other], [other, me])
            assert_almost_equal(es1+es2, 1)

    def test_explicit(self):
        from math_ import expected_score
        rating1, rating2 = 2400, 2000
        es1 = expected_score(rating1, rating2)
        es2 = expected_score(rating2, rating1)
        assert_almost_equal(es1, 10/11)
        assert_almost_equal(es2, 1/11)


class test_update_rating(object):
    def test_explicit_easy_win(self):
        from math_ import update_rating
        K = 32
        rating1, rating2 = 2400, 2000
        new_rating1, new_rating2 = update_rating(
            rating1=rating1,
            rating2=rating2,
            K1=K, K2=K,
            score1=1,
            score2=0
        )
        assert_almost_equal(new_rating1, 2400+32*(1-10/11))
        assert_almost_equal(new_rating2, 2000+32*(0-1/11))

    def test_explicit_difficult_win(self):
        from math_ import update_rating
        K = 32
        rating1, rating2 = 2400, 2000
        new_rating1, new_rating2 = update_rating(
            rating1=rating1,
            rating2=rating2,
            K1=K, K2=K,
            score1=0,
            score2=1
        )
        assert_almost_equal(new_rating1, 2400+32*(0-10/11))
        assert_almost_equal(new_rating2, 2000+32*(1-1/11))







