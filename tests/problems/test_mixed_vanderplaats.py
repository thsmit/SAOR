import pytest
import numpy as np
import logging
from Problems.VanderplaatsBeam import Vanderplaats
from sao.approximations.taylor import Taylor1
from sao.intervening_vars import Linear, ConLin, ReciSquared, ReciCubed
from sao.move_limits.ml_intervening import MoveLimitIntervening
from sao.problems.subproblem import Subproblem
from sao.problems.mixed import Mixed
from sao.solvers.SolverIP_Svanberg import SvanbergIP

# Set options for logging data: https://www.youtube.com/watch?v=jxmzY9soFXg&ab_channel=CoreySchafer
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

# If you want to print on terminal
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)

np.set_printoptions(precision=4)


@pytest.mark.parametrize('N', [50])
def test_mixed_vanderplaats(N):

    # Instantiate problem
    prob = Vanderplaats(N)
    assert prob.n == 2 * N

    # Define variable and response sets as dictionaries
    var_set = {0: np.arange(0, N),
               1: np.arange(N, prob.n)}
    resp_set = {0: np.array([0]),
                1: np.arange(1, N + 1),
                2: np.arange(N + 1, prob.n),
                3: np.array([prob.n])}

    # Instantiate a mixed approximation scheme
    subprob_map = {
                   (0, 0): Subproblem(intervening=Linear(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
                                                              xmax=prob.xmax[var_set[0]], move_limit=0.2)),
                   (0, 1): Subproblem(intervening=Linear(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
                                                              xmax=prob.xmax[var_set[1]], move_limit=0.2)),
                   (1, 0): Subproblem(intervening=ConLin(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
                                                              xmax=prob.xmax[var_set[0]], move_limit=0.2)),
                   (1, 1): Subproblem(intervening=ReciSquared(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
                                                              xmax=prob.xmax[var_set[1]], move_limit=0.2)),
                   (2, 0): Subproblem(intervening=Linear(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
                                                              xmax=prob.xmax[var_set[0]], move_limit=0.2)),
                   (2, 1): Subproblem(intervening=Linear(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
                                                              xmax=prob.xmax[var_set[1]], move_limit=0.2)),
                   (3, 0): Subproblem(intervening=ConLin(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
                                                              xmax=prob.xmax[var_set[0]], move_limit=0.2)),
                   (3, 1): Subproblem(intervening=ReciCubed(),
                                      approximation=Taylor1(),
                                      ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
                                                              xmax=prob.xmax[var_set[1]], move_limit=0.2))
                   }
    # subprob_map = {
    #     (0, 0): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
    #                                                xmax=prob.xmax[var_set[0]], move_limit=0.2)),
    #     (0, 1): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
    #                                                xmax=prob.xmax[var_set[1]], move_limit=0.2)),
    #     (1, 0): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
    #                                                xmax=prob.xmax[var_set[0]], move_limit=0.2)),
    #     (1, 1): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
    #                                                xmax=prob.xmax[var_set[1]], move_limit=0.2)),
    #     (2, 0): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
    #                                                xmax=prob.xmax[var_set[0]], move_limit=0.2)),
    #     (2, 1): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
    #                                                xmax=prob.xmax[var_set[1]], move_limit=0.2)),
    #     (3, 0): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[0]],
    #                                                xmax=prob.xmax[var_set[0]], move_limit=0.2)),
    #     (3, 1): Subproblem(intervening=PolyFit2(),
    #                        approximation=Taylor1(),
    #                        ml=MoveLimitIntervening(xmin=prob.xmin[var_set[1]],
    #                                                xmax=prob.xmax[var_set[1]], move_limit=0.2))
    # }

    # Instantiate a mixed scheme
    subprob = Mixed(subprob_map, var_set, resp_set)

    # Instantiate solver
    solver = SvanbergIP(prob.n, prob.m)

    # Initialize iteration counter and design
    itte = 0
    x_k = prob.x0.copy()
    xold1 = np.zeros_like(x_k)
    vis = None

    # Optimization loop
    while np.linalg.norm(x_k - xold1) > 1e-3:

        # Evaluate responses and sensitivities at current point, i.e. g(X^(k)), dg(X^(k))
        f = prob.g(x_k)
        df = prob.dg(x_k)

        # Print current iteration and x_k
        vis = prob.visualize(x_k, itte, vis)
        logger.info(
            'iter: {:^4d}  |  obj: {:^9.3f}  |  constr1: {:^6.3f}  |  constr2: {:^6.3f}  |  constr3: {:^6.3f}'.format(
                itte, f[0], f[1], f[1 + N], f[-1]))

        # Build approximate sub-problem at X^(k)
        subprob.build(x_k, f, df)

        # Call solver (x_k, g and dg are within approx instance)
        x, y, z, lam, xsi, eta, mu, zet, s = solver.subsolv(subprob)
        xold1 = x_k.copy()
        x_k = x.copy()

        # solver = ipb(subprob, epsimin=1e-7)
        # solver.update()
        # x_k = solver.x.copy()

        itte += 1

    logger.info('Optimization loop converged!')


if __name__ == "__main__":
    test_mixed_vanderplaats(5)
