import json
import math
import numpy as np
from sqlalchemy import text
from app.core.database import async_session
from app.schemas.env_config import EnvConfig


class EnvironmentEvaluator:
    def __init__(self):
        self.reference_data = self._load_reference_data()

    def _load_reference_data(self) -> dict:
        return {
            "lift_coefficient": 0.5,
            "drag_coefficient": 0.03,
            "pitch_rate": 0.1,
            "roll_rate": 0.2,
        }

    async def evaluate(self, env_id: str, weights: dict = None) -> dict:
        if weights is None:
            weights = {
                "diversity": 0.25,
                "challenge": 0.25,
                "realism": 0.25,
                "effectiveness": 0.25,
            }

        async with async_session() as session:
            result = await session.execute(
                text("SELECT config FROM envs WHERE id = :id"),
                {"id": env_id}
            )
            env = result.fetchone()
            if not env:
                return None

            config = json.loads(env[0]) if isinstance(env[0], str) else env[0]

            diversity_score = await self._calculate_diversity(session, env_id, config)
            challenge_score = await self._calculate_challenge(config)
            realism_score = await self._calculate_realism(config)
            effectiveness_score = await self._calculate_effectiveness(session, env_id)

            total_score = (
                weights["diversity"] * diversity_score +
                weights["challenge"] * challenge_score +
                weights["realism"] * realism_score +
                weights["effectiveness"] * effectiveness_score
            )

            suggestions = self._generate_suggestions(
                diversity_score, challenge_score, realism_score, effectiveness_score
            )

            evaluation = {
                "diversity_score": round(diversity_score, 2),
                "challenge_score": round(challenge_score, 2),
                "realism_score": round(realism_score, 2),
                "effectiveness_score": round(effectiveness_score, 2),
                "total_score": round(total_score, 2),
                "weights": weights,
                "suggestions": suggestions,
            }

            await session.execute(
                text(
                    """
                    INSERT INTO env_evaluations (id, env_id, diversity_score, challenge_score, realism_score, effectiveness_score, total_score, weights, suggestions, created_at)
                    VALUES (:id, :env_id, :diversity_score, :challenge_score, :realism_score, :effectiveness_score, :total_score, :weights, :suggestions, NOW())
                    """
                ),
                {
                    "id": f"eval_{env_id}",
                    "env_id": env_id,
                    "diversity_score": evaluation["diversity_score"],
                    "challenge_score": evaluation["challenge_score"],
                    "realism_score": evaluation["realism_score"],
                    "effectiveness_score": evaluation["effectiveness_score"],
                    "total_score": evaluation["total_score"],
                    "weights": json.dumps(weights),
                    "suggestions": json.dumps(suggestions),
                }
            )
            await session.commit()

        return evaluation

    async def _calculate_diversity(self, session, env_id: str, config: dict) -> float:
        result = await session.execute(
            text("SELECT config FROM envs WHERE id != :id LIMIT 10"),
            {"id": env_id}
        )
        other_envs = result.fetchall()

        if not other_envs:
            return 50.0

        current_params = self._extract_numeric_params(config)
        other_params_list = []
        for env in other_envs:
            other_config = json.loads(env[0]) if isinstance(env[0], str) else env[0]
            other_params_list.append(self._extract_numeric_params(other_config))

        similarities = []
        for other_params in other_params_list:
            similarity = self._cosine_similarity(current_params, other_params)
            similarities.append(similarity)

        avg_similarity = sum(similarities) / len(similarities) if similarities else 0.5
        diversity = (1 - avg_similarity) * 100

        return min(max(diversity, 0), 100)

    def _extract_numeric_params(self, config: dict) -> list:
        params = []
        if "atmosphere" in config:
            params.append(config["atmosphere"].get("wind_speed", 0))
            params.append(config["atmosphere"].get("wind_direction", 0))
            params.append(config["atmosphere"].get("visibility", 10000) / 10000)
        if "aircraft" in config:
            params.append(config["aircraft"].get("mass", 1000) / 10000)
            params.append(config["aircraft"].get("wingspan", 10) / 100)
        if "obstacles" in config:
            params.append(config["obstacles"].get("count", 0) / 50)
            params.append(config["obstacles"].get("density", 0))
        return params if params else [0, 0, 0, 0, 0, 0, 0]

    def _cosine_similarity(self, a: list, b: list) -> float:
        if len(a) != len(b):
            return 0
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0
        return dot_product / (norm_a * norm_b)

    async def _calculate_challenge(self, config: dict) -> float:
        wind_speed = config.get("atmosphere", {}).get("wind_speed", 5)
        obstacle_count = config.get("obstacles", {}).get("count", 0)

        wind_factor = min(wind_speed / 30, 1.0)
        obstacle_factor = min(obstacle_count / 20, 1.0)

        challenge = (wind_factor * 0.5 + obstacle_factor * 0.5) * 100
        return min(max(challenge, 10), 90)

    async def _calculate_realism(self, config: dict) -> float:
        aircraft = config.get("aircraft", {})
        mass = aircraft.get("mass", 1043)
        wingspan = aircraft.get("wingspan", 11)

        if 500 <= mass <= 50000 and 5 <= wingspan <= 50:
            realism = 70
        elif 100 <= mass <= 100000 and 1 <= wingspan <= 100:
            realism = 50
        else:
            realism = 30

        wind_speed = config.get("atmosphere", {}).get("wind_speed", 5)
        if wind_speed <= 25:
            realism += 15
        else:
            realism += 5

        return min(realism, 100)

    async def _calculate_effectiveness(self, session, env_id: str) -> float:
        result = await session.execute(
            text(
                """
                SELECT episode_reward FROM training_metrics
                WHERE env_id = :env_id
                ORDER BY step DESC LIMIT 100
                """
            ),
            {"env_id": env_id}
        )
        metrics = result.fetchall()

        if not metrics:
            return 50.0

        rewards = [m[0] for m in metrics if m[0] is not None]
        if not rewards:
            return 50.0

        auc = sum(rewards) / len(rewards)
        effectiveness = min(max(auc / 10, 0), 100)

        return effectiveness

    def _generate_suggestions(self, diversity: float, challenge: float, realism: float, effectiveness: float) -> list:
        suggestions = []
        if diversity < 40:
            suggestions.append("多样性偏低，建议增加参数变化范围或使用不同模板")
        if challenge < 30:
            suggestions.append("挑战性不足，建议增加风速或障碍物数量")
        if challenge > 80:
            suggestions.append("挑战性过高，建议降低环境复杂度")
        if realism < 40:
            suggestions.append("真实性偏低，建议提高物理建模精度或使用标准机型参数")
        if effectiveness < 30:
            suggestions.append("有效性不足，建议优化奖励函数设计")
        if effectiveness == 50:
            suggestions.append("暂无训练数据，有效性评分基于默认值")
        return suggestions


evaluator = EnvironmentEvaluator()
