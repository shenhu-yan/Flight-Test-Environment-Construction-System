import numpy as np
from abc import ABC, abstractmethod
from typing import Any


class BaseOptimizer(ABC):
    @abstractmethod
    def suggest(self, param_space: dict) -> dict:
        pass

    @abstractmethod
    def observe(self, params: dict, score: float) -> None:
        pass


class BayesOptimizer(BaseOptimizer):
    def __init__(self):
        self.history: list = []
        self.optimizer = None
        self._param_space: dict = {}
        self._param_names: list = []
        self._told_count: int = 0

    def suggest(self, param_space: dict) -> dict:
        """获取下一组候选参数。

        内部会先将尚未 tell 的观测结果告诉优化器，再 ask 新候选。
        """
        try:
            from skopt import Optimizer
            from skopt.space import Real

            # 如果参数空间变了，重建优化器并清空历史
            if param_space != self._param_space:
                self._param_space = param_space
                self._param_names = list(param_space.keys())
                dimensions = [
                    Real(bounds[0], bounds[1], name=name)
                    for name, bounds in param_space.items()
                ]
                self.optimizer = Optimizer(dimensions=dimensions, random_state=42)
                self.history.clear()
                self._told_count = 0

            # tell 新的观测结果
            new_obs = self.history[self._told_count:]
            if new_obs and self.optimizer:
                X = [list(h["params"].values()) for h in new_obs]
                y = [h["score"] for h in new_obs]
                self.optimizer.tell(X, y)
                self._told_count = len(self.history)

            # ask 新候选
            suggested = self.optimizer.ask(n_points=1)
            params = {
                name: float(val)
                for name, val in zip(self._param_names, suggested[0])
            }
            return params

        except ImportError:
            # scikit-optimize 不可用，退化为随机搜索
            params = {}
            for name, bounds in param_space.items():
                params[name] = np.random.uniform(bounds[0], bounds[1])
            return params

    def observe(self, params: dict, score: float) -> None:
        """记录一组参数的评估分数。"""
        self.history.append({"params": params, "score": score})

    def reset(self):
        """重置优化器状态。"""
        self.history.clear()
        self.optimizer = None
        self._param_space = {}
        self._param_names = []
        self._told_count = 0
