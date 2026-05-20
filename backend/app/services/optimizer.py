import numpy as np
from abc import ABC, abstractmethod
from typing import Any


class BaseOptimizer(ABC):
    @abstractmethod
    async def suggest(self, history: list) -> dict:
        pass

    @abstractmethod
    async def observe(self, params: dict, score: float) -> None:
        pass


class BayesOptimizer(BaseOptimizer):
    def __init__(self):
        self.history = []
        self.optimizer = None

    async def suggest(self, param_space: dict, weights: dict) -> dict:
        try:
            from skopt import Optimizer
            from skopt.space import Real

            dimensions = []
            param_names = []
            for name, bounds in param_space.items():
                dimensions.append(Real(bounds[0], bounds[1], name=name))
                param_names.append(name)

            if self.optimizer is None:
                self.optimizer = Optimizer(dimensions=dimensions, random_state=42)

            if self.history:
                X = [list(h["params"].values()) for h in self.history]
                y = [h["score"] for h in self.history]
                self.optimizer.tell(X, y)

            suggested = self.optimizer.ask(n_points=1)
            params = {name: float(val) for name, val in zip(param_names, suggested[0])}

            return {"params": params, "score": 0}

        except ImportError:
            params = {}
            for name, bounds in param_space.items():
                params[name] = np.random.uniform(bounds[0], bounds[1])
            return {"params": params, "score": 0}

    async def observe(self, params: dict, score: float) -> None:
        self.history.append({"params": params, "score": score})


optimizer = BayesOptimizer()
