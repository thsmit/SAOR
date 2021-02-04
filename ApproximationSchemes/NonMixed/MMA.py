## Imports
import numpy as np
from ApproximationSchemes.NonMixed.Approx import Approximation


## MMA Approximation class
class MMA(Approximation):

    ## Constructor of class
    def __init__(self, n, m, xmin, xmax, **kwargs):
        Approximation.__init__(self, n, m, xmin, xmax, **kwargs)          # let parent class handle the common things

        # Initialization of MMA-specific things
        self.pijconst = 1e-3
        self.dxmin = 1e-5
        self.albefa = 0.1                           # albefa is limiting the max change of vars wrt asymptotes. Was 0.1
        self.asyinit = 0.5                          # was 0.5
        self.asyincr = 1.2
        self.asydecr = 0.7
        self.epsimin = 1e-7
        self.low = self.xmin.copy()
        self.upp = self.xmax.copy()
        self.ittomax = 400
        self.factor = self.asyinit * np.ones(self.n)
        self.iterinitial = 1.5
        self.asybound = 10.0
        self.name = 'MMA'

    ## Build current sub-problem for MMA class: overrides Approximation.build_sub_prob(..) because of asymptotes
    def build_sub_prob(self, x, g, dg, **kwargs):
        self.x = x.copy()
        self.g = g.copy()
        self.dg = dg.copy()
        self._set_asymptotes()
        self.y_k = self._set_y(self.x)
        self._set_P()
        if self.so:
            self.ddg = kwargs.get('ddg', None) 
            self._set_Q()
        self._set_zo_term()
        self._set_bounds()

    ## Define intermediate vars for MMA: y = T_inv(x)
    def _set_y(self, x):
        y = np.empty((self.n, self.m + 1))
        for j in range(0, self.m + 1):
            y[self.dg[j, :] >= 0, j] = (1 / (self.upp - x))[self.dg[j, :] >= 0]
            y[self.dg[j, :] < 0, j] = 1 / (x - self.low)[self.dg[j, :] < 0]
        return y

    ## Define derivatives intermediate vars for linear: dy/dx = dT_inv(x)/dx
    def _set_dydx(self, x):
        dy = np.empty((self.n, self.m + 1))
        for j in range(0, self.m + 1):
            dy[self.dg[j, :] >= 0, j] = (1 / (self.upp - x) ** 2)[self.dg[j, :] >= 0]
            dy[self.dg[j, :] < 0, j] = (-1 / (x - self.low) ** 2)[self.dg[j, :] < 0]
        return dy

    ## Define derivatives intermediate vars for linear: ddy/dx = ddT_inv(x)/dx
    def _set_ddydx(self, x):
        ddy = np.empty((self.n, self.m + 1))
        for j in range(0, self.m + 1):
            ddy[self.dg[j, :] >= 0, j] = (2 / (self.upp - x) ** 3)[self.dg[j, :] >= 0]
            ddy[self.dg[j, :] < 0, j]  = (2 / (x - self.low) ** 3)[self.dg[j, :] < 0]
        return ddy

    ## Define chain rule term: y = T_inv(x) --> dT/dy = dx/dy
    def _set_dTdy(self):
        dTdy = np.empty((self.n, self.m + 1))
        for j in range(0, self.m + 1):
            dTdy[self.dg[j, :] >= 0, j] = (1 / self.y_k[:, j] ** 2)[self.dg[j, :] >= 0]
            dTdy[self.dg[j, :] < 0, j] = (-1 / self.y_k[:, j] ** 2)[self.dg[j, :] < 0]
        return dTdy

    ## Define chain rule 2nd-order term: y = T_inv(x) --> d^2T/dy^2 = d^2x/dy^2
    def _set_ddTdy(self):
        ddTdy = np.empty((self.n, self.m + 1))
        for j in range(0, self.m + 1):
            ddTdy[self.dg[j, :] >= 0, j] = (-2 / self.y_k[:, j] ** 3)[self.dg[j, :] >= 0]
            ddTdy[self.dg[j, :] < 0, j] = (2 / self.y_k[:, j] ** 3)[self.dg[j, :] < 0]
        return ddTdy

    ## Set asymptotes at current iteration low, upp :           if low = 0 and upp = inf --> MMA = CONLIN
    def _set_asymptotes(self):

        # Initial values of asymptotes
        if self.iter < self.iterinitial:
            self.low = self.x - self.factor * self.dx
            self.upp = self.x + self.factor * self.dx

        # Update asymptotes
        else:

            # depending on if the signs of (x_k-xold) and (xold-xold2) are opposite, indicating an oscillation in xi
            # if the signs are equal the asymptotes are slowing down the convergence and should be relaxed

            # check for oscillations in variables (if zzz > 0: no oscillations, if zzz < 0: oscillations)
            zzz = (self.x - self.xold1) * (self.xold1 - self.xold2)

            # oscillating variables x_i are assigned a factor of asydecr and non-oscillating to asyincr
            self.factor[zzz > 0] = self.asyincr
            self.factor[zzz < 0] = self.asydecr

            # update lower and upper asymptotes
            self.low = self.x - self.factor * (self.xold1 - self.low)
            self.upp = self.x + self.factor * (self.upp - self.xold1)

            # check min and max bounds of asymptotes, as they cannot be too close or far from the variable (redundant?)
            lowmin = self.x - self.asybound * self.dx
            lowmax = self.x - 1 / (self.asybound ** 2) * self.dx
            uppmin = self.x + 1 / (self.asybound ** 2) * self.dx
            uppmax = self.x + self.asybound * self.dx

            # if given asymptotes cross boundaries put them to their max/min values (redundant?)
            self.low = np.maximum(self.low, lowmin)
            self.low = np.minimum(self.low, lowmax)
            self.upp = np.minimum(self.upp, uppmax)
            self.upp = np.maximum(self.upp, uppmin)

    ## Set the bounds alpha, beta for all variables -x- for the sub-problem generated by MMA
    def _set_bounds(self):

        # minimum variable bounds
        zzl1 = self.low + self.albefa * (self.x - self.low)      # limit change in x_i wrt asymptotes U_i, L_i
        zzl2 = self.x - self.move_limit * self.dx
        self.alpha = np.maximum.reduce([zzl1, zzl2, self.xmin])  # finds the max for each row of (zzl1, zzl2, xmin)

        # maximum variable bounds
        zzu1 = self.upp - self.albefa * (self.upp - self.x)      # limit change in x_i wrt asymptotes U_i, L_i
        zzu2 = self.x + self.move_limit * self.dx
        self.beta = np.minimum.reduce([zzu1, zzu2, self.xmax])   # finds the min for each row of (zzu1, zzu2, xmax)

    ## Define some properties of the approximation scheme
    def _set_properties(self, **kwargs):
        self.properties.convex = kwargs.get('convex', None)
        self.properties.separable = kwargs.get('separable', None)
