import pytest
import numpy as np
from Problems.square import Square
from sao.approximations.taylor import Taylor1, Taylor2
from sao.approximations.intervening import Linear, ConLin, MMA
from sao.move_limits.ml_intervening import MoveLimitIntervening
from sao.problems.subproblem import Subproblem
from sao.solvers.interior_point_x import InteriorPointX as ipx
from sao.solvers.interior_point_xy import InteriorPointXY as ipxy
from sao.solvers.interior_point_xyz import InteriorPointXYZ as ipxyz
from sao.solvers.SolverIP_Svanberg import SvanbergIP

np.set_printoptions(precision=4)


@pytest.mark.parametrize('n', [2, 3])
def test_square(n):

    # Instantiate problem
    prob = Square(n)
    assert prob.n == n

    # Instantiate a non-mixed approximation scheme
    subprob = Subproblem(intervening=ConLin(), approximation=Taylor1(),
                         ml=MoveLimitIntervening(xmin=prob.xmin, xmax=prob.xmax))

    # Initialize iteration counter and design
    itte = 0
    x_k = prob.x0.copy()

    # Optimization loop
    while not (x_k == pytest.approx(1/n * np.ones_like(x_k), rel=1e-3)):

        # Evaluate responses and sensitivities at current point, i.e. g(X^(k)), dg(X^(k))
        f = prob.g(x_k)
        df = prob.dg(x_k)
        ddf = (prob.ddg(x_k) if subprob.approx.__class__.__name__ == 'Taylor2' else None)

        # Print current iteration and x_k
        print('iter: {:^4d}  |  x: {:<20s}  |  obj: {:^9.3f}  |  constr: {:^6.3f}'.format(itte, np.array2string(x_k[0:2]), f[0], f[1]))

        # Build approximate sub-problem at X^(k)
        subprob.build(x_k, f, df, ddf)
        solverx = ipx(subprob, epsimin=1e-4)
        x_k = solverx.update()

        solverxy = ipxy(subprob, epsimin=1e-4)
        x_k = solverxy.update()

        solverxyz = ipxyz(subprob, epsimin=1e-4)
        x_k = solverxyz.update()

        itte += 1

    print('Alles goed!')


if __name__ == "__main__":
    test_square(4)

