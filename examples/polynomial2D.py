import numpy as np
import logging
from sao.approximations import Taylor1, Taylor2
from sao.problems import Subproblem
from sao.intervening_variables import Linear, MMA, MMAsquared, MixedIntervening
from sao.move_limits import Bounds, MoveLimit
from sao.convergence_criteria import VariableChange
from sao.util import Plot
from sao.solvers import SvanbergIP, CVXOPT, SCIPY
from util.plotter import Plot2, Plot3
from Problems._2d.Polynomial_2D import Polynomial2D

# Set options for logging data: https://www.youtube.com/watch?v=jxmzY9soFXg&ab_channel=CoreySchafer
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s:%(name)s:%(message)s')

# If you want to print on terminal
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)
logger.addHandler(stream_handler)
np.set_printoptions(precision=4)


def example_polynomial_2D():
    logger.info("Solving test_poly using y=MMA and solver=Ipopt Svanberg")

    # Instantiate problem
    prob = Polynomial2D()

    # Instantiate a non-mixed approximation scheme
    subprob = Subproblem(approximation=Taylor2(Linear()))
    # mixed_ml = MixedMoveLimit(prob.n, default=Bounds(prob.x_min, prob.x_max))
    # mixed_ml.add_move_limit(MoveLimit(move_limit=0.1, dx=prob.x_max-prob.x_min))
    # mixed_ml.add_move_limit(AdaptiveMoveLimit(move_limit=0.1, dx=prob.x_max[0]-prob.x_min[0]), var=[0])
    # subprob.set_limits([mixed_ml])
    # mix.set_move_limit(Bounds(0.0, 0.0), var=[2])
    subprob.set_limits([Bounds(prob.x_min, prob.x_max), MoveLimit(move_limit=0.1, dx=prob.x_max - prob.x_min)])

    # Instantiate solver
    solver = SvanbergIP(prob.n, prob.m)

    # Instantiate convergence criterion
    # criterion = KKT(x_min=prob.x_min, x_max=prob.x_max)
    # criterion = ObjectiveChange()
    # criterion = VariableChange(x_min=prob.x_min, x_max=prob.x_max)
    # criterion = Feasibility()
    # criterion = Alltogether(x_min=prob.x_min, x_max=prob.x_max)

    # Instantiate plotter           # TODO: Change the 'criterion' to f'{criterion.__class__.__name__}'
    plotter = Plot(['objective', 'constraint', 'criterion', 'max_constr_violation'], path="../../../../Desktop")
    plotter2_flag = True
    if plotter2_flag:
        plotter2 = Plot2(prob)

    # Initialize design and iteration counter
    # x_k = prob.x0.copy()                # At optimum: 1 active constraint (initial design: upper right)
    # x_k = np.array([1.5, 1.6])          # At optimum: 1 active constraint (initial design: lower left)
    # x_k = np.array([1.5, 2.1])          # At optimum: 2 active constraints, i.e. minimum at intersection (upper left)
    x_k = np.array([2, 1.5])            # no constraint active, i.e. internal minimum (lower right)
    itte = 0

    # Optimization loop
    while itte < 100:       # not criterion.converged:

        # Evaluate responses and sensitivities at current point, i.e. g(X^(k)), dg(X^(k)), ddg(X^(k))
        f = prob.g(x_k)
        df = prob.dg(x_k)
        ddf = prob.ddg(x_k) if isinstance(subprob.approx, Taylor1) else None

        # Build approximate sub-problem at X^(k)
        subprob.build(x_k, f, df, ddf)

        # Plot current approximation
        if plotter2_flag:
            # plotter2.plot_pair(x_k, f, prob, subprob, itte)
            plotter2.contour_plot(x_k, f, prob, subprob, itte)

        # Call solver (x_k, g and dg are within approx instance)
        x_k, y, z, lam, xsi, eta, mu, zet, s = solver.subsolv(subprob)

        # Assess convergence (give the correct keyword arguments for the criterion you choose)
        # criterion.assess_convergence(x_k=x_k, f=f, iter=itte, lam=lam, df=df)

        # Print & Plot              # TODO: Print and Plot the criterion as criterion.value (where 0 is now)
        logger.info(
            'iter: {:^4d}  |  x: {:<10s}  |  obj: {:^9.3f}  |  criterion: {:^6.3f}  |  max_constr_viol: {:^6.3f}'.format(
                itte, np.array2string(x_k[0]), f[0], 0, max(0, max(f[1:]))))
        plotter.plot([f[0], f[1], 0, max(0, max(f[1:]))])

        itte += 1

    logger.info('Optimization loop converged!')


def example_polynomial_2D_mixed():
    logger.info("Solving test_poly using y=MixedML and Ipopt Svanberg")

    # Instantiate problem
    prob = Polynomial2D()

    # Instantiate a mixed intervening variable
    mix = MixedIntervening(prob.n, prob.m + 1, default=MMA(prob.x_min, prob.x_max))
    mix.set_intervening(MMAsquared(prob.x_min, prob.x_max), var=[0], resp=[1])

    # Instantiate a mixed approximation scheme
    subprob = Subproblem(approximation=Taylor1(mix))
    subprob.set_limits([Bounds(prob.x_min, prob.x_max), MoveLimit(move_limit=0.2)])

    # Instantiate solver
    solver = SvanbergIP(prob.n, prob.m)

    # Instantiate convergence criterion
    # criterion = KKT(x_min=prob.x_min, x_max=prob.x_max)
    # criterion = ObjectiveChange()
    # criterion = VariableChange(x_min=prob.x_min, x_max=prob.x_max)
    # criterion = Feasibility()
    # criterion = Alltogether(x_min=prob.x_min, x_max=prob.x_max)

    # Instantiate plotter           # TODO: Change the 'criterion' to f'{criterion.__class__.__name__}'
    plotter = Plot(['objective', 'constraint', 'criterion', 'max_constr_violation'], path=".")
    plotter3_flag = True
    if plotter3_flag:
        plotter3 = Plot3(prob)

    # Initialize iteration counter and design
    itte = 0
    x_k = prob.x0.copy()

    # Optimization loop
    while itte < 100:       # not criterion.converged:

        # Evaluate responses and sensitivities at current point, i.e. g(X^(k)), dg(X^(k))
        f = prob.g(x_k)
        df = prob.dg(x_k)
        ddf = prob.ddg(x_k) if isinstance(subprob.approx, Taylor1) else None

        # Build approximate sub-problem at X^(k)
        subprob.build(x_k, f, df, ddf)

        # Plot current approximation
        if plotter3_flag:
            # plotter3.plot_pair(x_k, f, prob, subprob, itte)
            plotter3.contour_plot(x_k, f, prob, subprob, itte)

        # Call solver (x_k, g and dg are within approx instance)
        x_k, y, z, lam, xsi, eta, mu, zet, s = solver.subsolv(subprob)

        # Assess convergence (give the correct keyword arguments for the criterion you choose)
        # criterion.assess_convergence(x_k=x_k, f=f, iter=itte, lam=lam, df=df)

        # Print & Plot              # TODO: Print and Plot the criterion as criterion.value (where 0 is now)
        logger.info(
            'iter: {:^4d}  |  x: {:<10s}  |  obj: {:^9.3f}  |  criterion: {:^6.3f}  |  max_constr_viol: {:^6.3f}'.format(
                itte, np.array2string(x_k[0]), f[0], 0, max(0, max(f[1:]))))
        plotter.plot([f[0], f[1], 0, max(0, max(f[1:]))])

        itte += 1

    logger.info('Optimization loop converged!')


def example_polynomial_2D_cvxopt():
    logger.info("Solving test_poly using y=MMA and solver=Ipopt Svanberg")

    # Instantiate problem
    prob = Polynomial2D()

    # Instantiate a non-mixed approximation scheme
    subprob = Subproblem(approximation=Taylor1(MMA(prob.x_min, prob.x_max)))
    subprob.set_limits([Bounds(prob.x_min, prob.x_max), MoveLimit(move_limit=0.1, dx=prob.x_max - prob.x_min)])

    # Instantiate solver
    solver = CVXOPT(prob.n, prob.m)

    # Initialize design and iteration counter
    x_k = np.array([2, 1.5])  # no constraint active, i.e. internal minimum (lower right)
    itte = 0

    # Instantiate convergence criterion
    criterion = VariableChange(x_k)

    # Instantiate plotter           # TODO: Change the 'criterion' to f'{criterion.__class__.__name__}'
    plotter = Plot(['objective', 'constraint', 'criterion', 'max_constr_violation'], path="../../../../Desktop")
    plotter2_flag = True
    if plotter2_flag:
        plotter2 = Plot2(prob)

    # Optimization loop
    while itte < 100:       # not criterion.converged:

        # Evaluate responses and sensitivities at current point, i.e. g(X^(k)), dg(X^(k)), ddg(X^(k))
        f = prob.g(x_k)
        df = prob.dg(x_k)
        ddf = prob.ddg(x_k) if isinstance(subprob.approx, Taylor1) else None

        # Build approximate sub-problem at X^(k)
        subprob.build(x_k, f, df, ddf)

        # Plot current approximation
        if plotter2_flag:
            # plotter2.plot_pair(x_k, f, prob, subprob, itte)
            plotter2.contour_plot(x_k, f, prob, subprob, itte)

        # Call solver (x_k, g and dg are within approx instance)
        x_k = np.array(solver.subsolv(subprob)).flatten()

        # Print & Plot              # TODO: Print and Plot the criterion as criterion.value (where 0 is now)
        logger.info(
            'iter: {:^4d}  |  x: {:<10s}  |  obj: {:^9.3f}  |  criterion: {:^6.3f}  |  max_constr_viol: {:^6.3f}'.format(
                itte, np.array2string(x_k[0]), f[0], 0, max(0, max(f[1:]))))
        plotter.plot([f[0], f[1], 0, max(0, max(f[1:]))])

        itte += 1

    logger.info('Optimization loop converged!')


def example_polynomial_2D_scipy():
    logger.info("Solving test_poly using y=MMA and solver=Ipopt Svanberg")

    # Instantiate problem
    prob = Polynomial2D()

    # Instantiate a non-mixed approximation scheme
    subprob = Subproblem(approximation=Taylor1(MMA(prob.x_min, prob.x_max)))
    subprob.set_limits([Bounds(prob.x_min, prob.x_max), MoveLimit(move_limit=0.1, dx=prob.x_max - prob.x_min)])

    # Initialize design and iteration counter
    x_k = np.array([2, 1.5])  # no constraint active, i.e. internal minimum (lower right)
    itte = 0

    # Instantiate solver
    solver = SCIPY(prob.n, prob.m, x0=x_k)

    # Instantiate convergence criterion
    criterion = VariableChange(x_k)

    # Instantiate plotter           # TODO: Change the 'criterion' to f'{criterion.__class__.__name__}'
    plotter = Plot(['objective', 'constraint', 'criterion', 'max_constr_violation'], path="../../../../Desktop")
    plotter2_flag = True
    if plotter2_flag:
        plotter2 = Plot2(prob)

    # Optimization loop
    while itte < 100:       # not criterion.converged:

        # Evaluate responses and sensitivities at current point, i.e. g(X^(k)), dg(X^(k)), ddg(X^(k))
        f = prob.g(x_k)
        df = prob.dg(x_k)
        ddf = prob.ddg(x_k) if isinstance(subprob.approx, Taylor2) else None

        # Build approximate sub-problem at X^(k)
        subprob.build(x_k, f, df, ddf)

        # Plot current approximation
        if plotter2_flag:
            # plotter2.plot_pair(x_k, f, prob, subprob, itte)
            plotter2.contour_plot(x_k, f, prob, subprob, itte)

        # Call solver (x_k, g and dg are within approx instance)
        x_k = solver.subsolv(subprob)

        # Print & Plot              # TODO: Print and Plot the criterion as criterion.value (where 0 is now)
        logger.info(
            'iter: {:^4d}  |  x: {:<10s}  |  obj: {:^9.3f}  |  criterion: {:^6.3f}  |  max_constr_viol: {:^6.3f}'.format(
                itte, np.array2string(x_k[0]), f[0], 0, max(0, max(f[1:]))))
        plotter.plot([f[0], f[1], 0, max(0, max(f[1:]))])

        itte += 1

    logger.info('Optimization loop converged!')


if __name__ == "__main__":
    # example_polynomial_2D()
    # example_polynomial_2D_mixed()
    # example_polynomial_2D_cvxopt()
    example_polynomial_2D_scipy()
