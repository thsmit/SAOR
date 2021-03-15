import pytest
import numpy as np
from Problems.square import Square
from sao.approximations.taylor import Taylor1, Taylor2
from sao.approximations.intervening import Linear, ConLin, MMA
from sao.move_limits.ml_intervening import MoveLimitIntervening
from sao.problems.subproblem import Subproblem
from sao.problems.mixed import Mixed
from sao.solvers.interior_point_basis import InteriorPointBasis as ipb
from sao.solvers.interior_point_artificial import InteriorPointArtificial as ipa
from sao.solvers.SolverIP_Svanberg import SvanbergIP
from line_profiler import LineProfiler

np.set_printoptions(precision=4)


def test_mixed_square(n):

    # Instantiate problem
    prob = Square(n)
    assert prob.n == n

    # Define variable and response sets as dictionaries
    var_set = {0: np.array([0]),
               1: np.array([1]),
               2: np.arange(2, prob.n)}
    resp_set = {0: np.array([0]),
                1: np.array([1])}

    # Instantiate a mixed approximation scheme
    subprob_dict = {(0, 0): Subproblem(intervening=MMA(prob.xmin[var_set[0]], prob.xmax[var_set[0]]),
                                       approximation=Taylor1(),
                                       ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
                                                               xmax=prob.xmax[var_set[0]])),
                    (0, 1): Subproblem(intervening=MMA(prob.xmin[var_set[1]], prob.xmax[var_set[1]]),
                                       approximation=Taylor1(),
                                       ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
                                                               xmax=prob.xmax[var_set[1]])),
                    (0, 2): Subproblem(intervening=MMA(prob.xmin[var_set[2]], prob.xmax[var_set[2]]),
                                       approximation=Taylor1(),
                                       ml=MoveLimitIntervening(xmin=prob.xmin[var_set[2]],
                                                               xmax=prob.xmax[var_set[2]])),
                    (1, 0): Subproblem(intervening=Linear(),
                                       approximation=Taylor1(),
                                       ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
                                                               xmax=prob.xmax[var_set[0]])),
                    (1, 1): Subproblem(intervening=Linear(),
                                       approximation=Taylor1(),
                                       ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
                                                               xmax=prob.xmax[var_set[1]])),
                    (1, 2): Subproblem(intervening=Linear(),
                                       approximation=Taylor1(),
                                       ml=MoveLimitIntervening(xmin=prob.xmin[var_set[2]],
                                                               xmax=prob.xmax[var_set[2]]))}

    # Instantiate a mixed scheme
    subprob = Mixed(prob.n, prob.m, subprob_dict, var_set, resp_set)

    # Instantiate solver
    solver = SvanbergIP(prob.n, prob.m)

    # Initialize iteration counter and design
    itte = 0
    x_k = prob.x0.copy()

    # Optimization loop
    while not (x_k == pytest.approx(1/n * np.ones_like(x_k), rel=1e-4)):

        # Evaluate responses and sensitivities at current point, i.e. g(X^(k)), dg(X^(k))
        f = prob.g(x_k)
        df = prob.dg(x_k)

        # Print current iteration and x_k
        print('iter: {:^4d}  |  x: {:<20s}  |  obj: {:^9.3f}  |  constr: {:^6.3f}'.format(
            itte, np.array2string(x_k[0:2]), f[0], f[1]))

        # Build approximate sub-problem at X^(k)
        subprob.build(x_k, f, df)

        # Call solver (x_k, g and dg are within approx instance)
        x, y, z, lam, xsi, eta, mu, zet, s = solver.subsolv(subprob)
        x_k = x.copy()

        # solver = ipb(subprob, epsimin=1e-7)
        # solver.update()
        # x_k = solver.x.copy()

        itte += 1

    print('Alles goed!')


if __name__ == "__main__":
    test_mixed_square(4)
