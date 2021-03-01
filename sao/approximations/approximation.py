from abc import ABC, abstractmethod


class Approximation(ABC):
    def __init__(self):
        self.x = None
        self.alpha, self.beta = None, None                  # Bounds of the local sub-problem
        self.g, self.dg, self.ddg = None, None, None

        self.m = -1  # Number of constraints
        self.n = -1  # Number of variables

    def update_approximation(self, x, xmin, xmax, g, dg, ddg=None):
        """ Puts in data from the original problem. Once per design iteration.

        :param x:
        :param xmin: Bounds of local problem, limited by global, and movelimit
        :param xmax:
        :param g:
        :param dg:
        :param ddg:
        :return:
        """
        self.x = x
        self.alpha, self.beta = xmin, xmax
        self.g, self.dg, self.ddg = g, dg, ddg

        self.m = len(self.g) - 1
        self.n = len(self.x)

        msg = (f'Expect sensitivity of size {self.m+1}x{self.n}: '
               f'Received {self.dg.shape}.')
        assert self.dg.shape == (self.m + 1, self.n), msg

        if self.ddg is not None:
            msg = (f"Expected ddf size: {self.m+1}x{self.n}: "
                   f"Received: {self.ddg.shape}.")
            assert self.ddg.shape == (self.m + 1, self.n), msg

        self.build_approximation()
        return self

    def build_approximation(self):
        pass

    @abstractmethod
    def g_approx(self, x):
        ...

    @abstractmethod
    def dg_approx(self, x):
        ...

    @abstractmethod
    def ddg_approx(self, x):
        ...
