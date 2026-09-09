"""Validate optimized scientific computation against a direct QR residual solve."""
import unittest
import numpy as np
from analysis_new.basis_solver import Solver, profile


class PlateauEquivalence(unittest.TestCase):
    def test_grid_matches_direct_residual_fit(self):
        rng = np.random.default_rng(42)
        n = 1500
        g = rng.uniform(1, 40, n)
        X = np.column_stack([np.ones(n), rng.normal(size=(n, 6))])
        y = X @ rng.normal(size=7) + .13*np.clip(g-14, 0, 11) + rng.normal(size=n)
        fast = Solver(X, y, g)
        direct = Solver(X, y)
        for a in range(8, 21):
            for b in range(18, 35):
                if b-a < 4:
                    continue
                H = np.column_stack([np.minimum(g, a), np.clip(g-a, 0, b-a)])
                self.assertAlmostEqual(fast.at_knots(a, b), direct.sse(H), places=8)
                H = np.column_stack([H, np.maximum(g-b, 0)])
                self.assertAlmostEqual(fast.at_knots(a, b, tail=True), direct.sse(H), places=8)
        best, table = profile(X, g, y, range(8, 21), range(18, 35))
        self.assertEqual(best[:2], tuple(table.loc[table.sse.idxmin(), ['k1', 'k2']]))


if __name__ == '__main__':
    unittest.main()
