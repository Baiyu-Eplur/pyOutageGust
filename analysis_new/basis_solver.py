"""Equivalent FWL grid solver; the same QR projection as the reference.

Residualise [g, (g-k)+] once. A plateau uses g-h_a and h_a-h_b;
an unrestricted third segment adds h_b. Each candidate needs only a 2/3 solve.
"""
import numpy as np
import pandas as pd


class Solver:
    def __init__(self, X0, y, g=None):
        self.Q, _ = np.linalg.qr(X0)
        self.ry = y - self.Q @ (self.Q.T @ y)
        self.yy = float(self.ry @ self.ry)
        if g is not None:
            self.grid = np.arange(8., 35.)
            H = np.column_stack([g, np.maximum(g[:, None] - self.grid, 0.)])
            rH = H - self.Q @ (self.Q.T @ H)
            self.G = rH.T @ rH
            self.c = rH.T @ self.ry
            self.pos = {float(k): i + 1 for i, k in enumerate(self.grid)}

    def sse(self, H):
        H = H[:, None] if H.ndim == 1 else H
        rH = H - self.Q @ (self.Q.T @ H)
        b = np.linalg.lstsq(rH, self.ry, rcond=None)[0]
        r = self.ry - rH @ b
        return float(r @ r)

    def at_knots(self, a, b, tail=False):
        ids = [0, self.pos[float(a)], self.pos[float(b)]]
        T = np.array([[1., 0., 0.], [-1., 1., 0.], [0., -1., 1.]])
        if not tail:
            T = T[:, :2]
        G = T.T @ self.G[np.ix_(ids, ids)] @ T
        c = T.T @ self.c[ids]
        return float(self.yy - c @ np.linalg.solve(G, c))


def profile(X0, g, y, k1r, k2r):
    solver = Solver(X0, y, g)
    rows = [(a, b, solver.at_knots(a, b)) for a in k1r for b in k2r if b-a >= 4]
    return min(rows, key=lambda row: row[2]), pd.DataFrame(rows, columns=['k1', 'k2', 'sse'])
