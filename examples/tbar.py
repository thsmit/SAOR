#
import numpy as np
#
from problems.svanberg1987 import TwoBarTruss
from sao.approximations import Taylor1, SphericalTaylor2, NonSphericalTaylor2
from sao.convergence_criteria import IterationCount
from sao.intervening_variables import Exponential
from sao.intervening_variables.mixed_intervening import MixedIntervening
from sao.intervening_variables.mma import MMA87A, MMA87C, MMA02
from sao.move_limits import Bounds, MoveLimit, MoveLimitFraction, AdaptiveMoveLimit
from sao.problems.subproblem2 import Subproblem
from sao.solvers.primal_dual_interior_point import pdip, Pdipx
#
from sao.util.records import Records
from sao.mappings.function import Function
#
"""
This example compares different SAO schemes for solving the Svanberg 1987 Two Bar Truss problem.
For a "fair" comparison, we use the convergence criteria as used in the paper.
"""
#
"""
We start with the scheme as presented in the paper.
"""
#
class myFunction(Function):
#
    def domain(self): #domain
#
        d_l = np.zeros(self.n,dtype=float)
        d_u = np.zeros(self.n,dtype=float)
        for i in range(self.n):
            d_l[i] = 1.01*self.L_k[i]
            d_u[i] = 0.99*self.U_k[i]
        return d_l, d_u
#
    def paramk(self):
#
        x_k = self.x_k
        hst_x_k = self.hst_x_k
        k = self.k
#
        asy_fac = 1/5e0
        s_l = 0.5; s_u = 0.75
        x_l = np.array([0.2, 0.1]) 
        x_u = np.array([4.0, 1.6]) 
#
        asy_fac = 1/5e0
        s_l = 0.5; s_u = 0.75
        x_l = np.array([0.2, 0.1]) 
        x_u = np.array([4.0, 1.6]) 
#
        if k == 0:
            L_k = np.zeros_like(x_k) 
            U_k = np.zeros_like(x_k) 
        else:
            L_k = self.L_k
            U_k = self.U_k
#
        i=0
        L_k[i]=asy_fac*x_k[i]
        U_k[i]=x_k[i]/asy_fac
#
        i=1
        if k <= 1:
            L_k[i]=x_k[i] - (x_u[i] - x_l[i])
            U_k[i]=x_k[i] + (x_u[i] - x_l[i])
        else:
            x_1 = hst_x_k[-2]
            x_2 = hst_x_k[-3]
            if (x_k[i]-x_1[i])*(x_1[i]-x_2[i]) < 0e0:
                L_k[i] = x_k[i] - s_l*(x_1[i] - L_k[i])
                U_k[i] = x_k[i] + s_l*(U_k[i] - x_1[i])
            else:
                L_k[i] = x_k[i] - (x_1[i] - L_k[i])/s_u
                U_k[i] = x_k[i] + (U_k[i] - x_1[i])/s_u
#
        self.L_k = L_k
        self.U_k = U_k
#
    def intervene(self, x):
#
        L_k = self.L_k
        U_k = self.U_k
#
        y = np.zeros_like(x)
        dy = np.zeros_like(x)
        ddy = np.zeros_like(x)
        dg_k = self.dg_k
        for i in range(self.n):
            if dg_k[0][i] < 0e0:
                y[i] = 1e0 / (x[i] - L_k[i])
                dy[i] = -1e0 / (x[i] - L_k[i])**2e0
                ddy[i] = 2e0 / (x[i] - L_k[i])**3e0
            else:
                y[i] = 1e0 / (U_k[i] - x[i])
                dy[i] = 1e0 / (U_k[i] - x[i])**2e0
                ddy[i] = 2e0 / (U_k[i] - x[i])**3e0
#
        return y, dy, ddy
#
def two_bar_truss():
#
    #instantiate the problem instance
    problem = TwoBarTruss()
#
    #bounds and move limit stuff
    bounds = Bounds(xmin=problem.x_min, xmax=problem.x_max)
    movelimit = MoveLimitFraction(fraction=2)
#
    n = problem.n
    x = problem.x0
    f = problem.g(x)
    df = problem.dg(x)
#
    obj = myFunction('Weight',problem.n)
    con1 = myFunction('Stress 1',problem.n)
    con2 = myFunction('Stress 2',problem.n)
#
    #instantiate subproblem
    funcs = [obj, con1, con2]
    subproblem = Subproblem(funcs, limits=[bounds, movelimit])
#
    #instantiate history
    history = Records(['f0','f1','f2'])
#
    converged = IterationCount(10)
    cnt=0
    while not converged:
        f = problem.g(x); df = problem.dg(x)
        history.popcol('f0',f[0]); history.popcol('f1',f[1]); history.popcol('f2',f[2])
        infeasibility = max(0.0, f[1], f[2])
        print("{}: {:.3f} {:.3f}".format(converged.iteration - 1, f[0], infeasibility))
        if (infeasibility < 0.001) and (f[0] < 1.001 * 1.51):
            print("The optimum solution found")
            break
#
        #update the approximations
        obj.setatk(x, f[0], df[0], 3)
        con1.setatk(x, f[1], df[1], 3)
        con2.setatk(x, f[2], df[2], 3)
#
        #update the subproblem
        subproblem.build(x,f,df)
#
        #solve the subproblem
        x[:] = pdip(subproblem, variables=Pdipx)[0]
    print("\n")
#
    return history
#
if __name__ == "__main__":
    two_bar_truss()
