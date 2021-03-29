import pytest
import numpy as np
from Problems.VanderplaatsBeam import Vanderplaats
from sao.approximations.taylor import Taylor1, Taylor2
from sao.approximations.intervening import Linear, ConLin, MMA
from sao.move_limits.ml_intervening import MoveLimitIntervening
from sao.problems.subproblem import Subproblem
from sao.solvers.interior_point_x import InteriorPointBasis as ipb
from sao.solvers.interior_point_xyz import InteriorPointArtificial as ipa
from sao.solvers.SolverIP_Svanberg import SvanbergIP

np.set_printoptions(precision=4)


@pytest.mark.parametrize('N', [50])
def test_vanderplaats(N):

    # Instantiate problem
    prob = Vanderplaats(N)
    assert prob.n == 2 * N

    # Instantiate a non-mixed approximation scheme
    subprob = Subproblem(intervening=MMA(prob.xmin, prob.xmax), approximation=Taylor1(),
                         ml=MoveLimitIntervening(xmin=prob.xmin, xmax=prob.xmax))

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
        print('iter: {:^4d}  |  x: {:<20s}  |  obj: {:^9.3f}  |  constr: {:^6.3f}'.format(itte, np.array2string(x_k[0:2]), f[0], f[1]))

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

    print('Alles goed!')


if __name__ == "__main__":
    test_vanderplaats(50)

