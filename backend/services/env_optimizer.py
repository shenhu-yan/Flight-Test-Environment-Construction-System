import json
import random
from datetime import datetime, timedelta
from models import db
from models.optimization_record import OptimizationRecord
from models.optimization_schedule import OptimizationSchedule
from models.environment import Environment


class EnvOptimizer:
    def __init__(self):
        self.evaluation_metrics = {
            'diversity': self._evaluate_diversity,
            'challenge': self._evaluate_challenge,
            'realism': self._evaluate_realism,
            'effectiveness': self._evaluate_effectiveness
        }

    def evaluate_environment(self, env_config, performance_data=None):
        scores = {}
        for metric_name, metric_func in self.evaluation_metrics.items():
            scores[metric_name] = metric_func(env_config, performance_data)

        total_score = sum(scores.values()) / len(scores)
        scores['total'] = total_score

        suggestions = self._generate_suggestions(scores, env_config)

        return {
            'scores': scores,
            'suggestions': suggestions
        }

    def _evaluate_diversity(self, env_config, performance_data=None):
        diversity_score = 0.0
        scenario = env_config.get('scenario', {})
        terrain = scenario.get('terrain', 'flat')
        weather = scenario.get('weather', 'clear')
        obstacles = scenario.get('obstacles', [])

        terrain_diversity = {'flat': 1.0, 'hilly': 2.0, 'mountainous': 3.0, 'urban': 3.0, 'forest': 2.0}
        diversity_score += terrain_diversity.get(terrain, 1.0) / 3.0

        weather_diversity = {'clear': 1.0, 'windy': 2.0, 'light_rain': 2.5, 'heavy_rain': 3.0, 'storm': 3.5}
        diversity_score += weather_diversity.get(weather, 1.0) / 3.5

        obstacle_diversity = min(len(obstacles) / 5.0, 1.0)
        diversity_score += obstacle_diversity

        return diversity_score / 3.0

    def _evaluate_challenge(self, env_config, performance_data=None):
        challenge_score = 0.0
        scenario = env_config.get('scenario', {})
        weather = scenario.get('weather', 'clear')
        obstacles = scenario.get('obstacles', [])

        weather_difficulty = {'clear': 1.0, 'windy': 2.0, 'light_rain': 2.5, 'heavy_rain': 3.0, 'storm': 4.0}
        challenge_score += weather_difficulty.get(weather, 1.0) / 4.0

        obstacle_difficulty = min(len(obstacles) / 4.0, 1.0)
        challenge_score += obstacle_difficulty

        reward = env_config.get('reward', {})
        reward_value = reward.get('reward_value', 10)
        penalty_rules = reward.get('penalty_rules', [])

        reward_difficulty = max(0, 1 - (reward_value / 50))
        challenge_score += reward_difficulty

        penalty_difficulty = min(len(penalty_rules) / 5.0, 1.0)
        challenge_score += penalty_difficulty

        return challenge_score / 4.0

    def _evaluate_realism(self, env_config, performance_data=None):
        realism_score = 0.0
        physics = env_config.get('physics', {})
        flight_dynamics = physics.get('flight_dynamics', 'basic')
        aerodynamics = physics.get('aerodynamics', 'basic')

        flight_dynamics_realism = {'basic': 1.0, 'medium': 2.0, 'advanced': 3.0}
        realism_score += flight_dynamics_realism.get(flight_dynamics, 1.0) / 3.0

        aerodynamics_realism = {'basic': 1.0, 'medium': 2.0, 'detailed': 3.0, 'precise': 3.5}
        realism_score += aerodynamics_realism.get(aerodynamics, 1.0) / 3.5

        scenario = env_config.get('scenario', {})
        terrain = scenario.get('terrain', 'flat')
        weather = scenario.get('weather', 'clear')

        terrain_weather_match = 1.0
        if terrain == 'mountainous' and weather == 'clear':
            terrain_weather_match = 0.7
        elif terrain == 'urban' and weather == 'storm':
            terrain_weather_match = 0.8

        realism_score += terrain_weather_match

        return realism_score / 3.0

    def _evaluate_effectiveness(self, env_config, performance_data=None):
        effectiveness_score = 0.0

        if performance_data:
            success_rate = performance_data.get('success_rate', 0.5)
            convergence_speed = performance_data.get('convergence_speed', 0.5)
            generalization_score = performance_data.get('generalization_score', 0.5)
            effectiveness_score = (success_rate + convergence_speed + generalization_score) / 3.0
        else:
            required_configs = ['scenario', 'physics', 'reward']
            for config in required_configs:
                if config in env_config:
                    effectiveness_score += 1.0 / len(required_configs)

        return effectiveness_score

    def _generate_suggestions(self, scores, env_config):
        suggestions = []

        if scores.get('diversity', 0) < 0.6:
            suggestions.append('增加环境多样性，可添加更多类型的障碍物或改变地形和气象条件')

        if scores.get('challenge', 0) < 0.5:
            suggestions.append('增加环境挑战性，可提高气象复杂度或增加障碍物数量')
        elif scores.get('challenge', 0) > 0.8:
            suggestions.append('降低环境挑战性，可简化气象条件或减少障碍物数量')

        if scores.get('realism', 0) < 0.6:
            suggestions.append('提高环境真实性，可使用更高级的物理模型或确保地形与气象的匹配')

        if scores.get('effectiveness', 0) < 0.5:
            suggestions.append('提高环境有效性，确保包含所有必要的配置项并优化奖励机制')

        return suggestions

    def optimize_environment(self, env_config, evaluation_results, custom_goals=None):
        new_config = json.loads(json.dumps(env_config))

        scores = evaluation_results.get('scores', {})
        suggestions = evaluation_results.get('suggestions', [])

        if scores.get('diversity', 0) < 0.6:
            self._optimize_diversity(new_config)

        if scores.get('challenge', 0) < 0.5:
            self._optimize_challenge(new_config, increase=True)
        elif scores.get('challenge', 0) > 0.8:
            self._optimize_challenge(new_config, increase=False)

        if scores.get('realism', 0) < 0.6:
            self._optimize_realism(new_config)

        if scores.get('effectiveness', 0) < 0.5:
            self._optimize_effectiveness(new_config)

        if custom_goals:
            self._apply_custom_goals(new_config, custom_goals)

        return new_config

    def _optimize_diversity(self, env_config):
        scenario = env_config.get('scenario', {})
        terrain_options = ['flat', 'hilly', 'mountainous', 'urban', 'forest']
        scenario['terrain'] = random.choice(terrain_options)
        weather_options = ['clear', 'windy', 'light_rain', 'heavy_rain', 'storm']
        scenario['weather'] = random.choice(weather_options)
        obstacle_options = ['building', 'tree', 'lamp_post', 'wind_turbine', 'power_line']
        current_obstacles = scenario.get('obstacles', [])
        available_obstacles = [obs for obs in obstacle_options if obs not in current_obstacles]
        if available_obstacles:
            current_obstacles.append(random.choice(available_obstacles))
        scenario['obstacles'] = current_obstacles

    def _optimize_challenge(self, env_config, increase=True):
        scenario = env_config.get('scenario', {})
        reward = env_config.get('reward', {})

        if increase:
            weather_mapping = {'clear': 'windy', 'windy': 'light_rain', 'light_rain': 'heavy_rain', 'heavy_rain': 'storm'}
            current_weather = scenario.get('weather', 'clear')
            if current_weather in weather_mapping:
                scenario['weather'] = weather_mapping[current_weather]
            obstacle_options = ['building', 'tree', 'lamp_post', 'wind_turbine', 'power_line']
            current_obstacles = scenario.get('obstacles', [])
            available_obstacles = [obs for obs in obstacle_options if obs not in current_obstacles]
            if available_obstacles:
                current_obstacles.append(random.choice(available_obstacles))
            scenario['obstacles'] = current_obstacles
            current_reward = reward.get('reward_value', 10)
            reward['reward_value'] = max(1, current_reward * 0.8)
        else:
            weather_mapping = {'storm': 'heavy_rain', 'heavy_rain': 'light_rain', 'light_rain': 'windy', 'windy': 'clear'}
            current_weather = scenario.get('weather', 'clear')
            if current_weather in weather_mapping:
                scenario['weather'] = weather_mapping[current_weather]
            current_obstacles = scenario.get('obstacles', [])
            if len(current_obstacles) > 0:
                current_obstacles = current_obstacles[:-1]
            scenario['obstacles'] = current_obstacles
            current_reward = reward.get('reward_value', 10)
            reward['reward_value'] = current_reward * 1.2

    def _optimize_realism(self, env_config):
        physics = env_config.get('physics', {})
        flight_dynamics_mapping = {'basic': 'medium', 'medium': 'advanced', 'advanced': 'advanced'}
        current_flight_dynamics = physics.get('flight_dynamics', 'basic')
        if current_flight_dynamics in flight_dynamics_mapping:
            physics['flight_dynamics'] = flight_dynamics_mapping[current_flight_dynamics]
        aerodynamics_mapping = {'basic': 'medium', 'medium': 'detailed', 'detailed': 'precise', 'precise': 'precise'}
        current_aerodynamics = physics.get('aerodynamics', 'basic')
        if current_aerodynamics in aerodynamics_mapping:
            physics['aerodynamics'] = aerodynamics_mapping[current_aerodynamics]

    def _optimize_effectiveness(self, env_config):
        if 'scenario' not in env_config:
            env_config['scenario'] = {'terrain': 'flat', 'weather': 'clear', 'obstacles': []}
        if 'physics' not in env_config:
            env_config['physics'] = {'flight_dynamics': 'basic', 'aerodynamics': 'basic', 'collision_detection': 'enabled'}
        if 'reward' not in env_config:
            env_config['reward'] = {'reward_value': 10, 'penalty_rules': ['collision', 'out_of_bounds'], 'target_threshold': 0.1}

    def _apply_custom_goals(self, env_config, custom_goals):
        if 'diversity' in custom_goals and custom_goals['diversity'] > 0.7:
            self._optimize_diversity(env_config)
        if 'challenge' in custom_goals:
            if custom_goals['challenge'] > 0.7:
                self._optimize_challenge(env_config, increase=True)
            elif custom_goals['challenge'] < 0.4:
                self._optimize_challenge(env_config, increase=False)
        if 'realism' in custom_goals and custom_goals['realism'] > 0.7:
            self._optimize_realism(env_config)

    def verify_optimization(self, original_config, optimized_config, performance_data=None):
        original_evaluation = self.evaluate_environment(original_config, performance_data)
        original_score = original_evaluation.get('scores', {}).get('total', 0)

        optimized_evaluation = self.evaluate_environment(optimized_config, performance_data)
        optimized_score = optimized_evaluation.get('scores', {}).get('total', 0)

        improvement = optimized_score - original_score
        improvement_percentage = (improvement / original_score) * 100 if original_score > 0 else 0

        return {
            'original_score': original_score,
            'optimized_score': optimized_score,
            'improvement': improvement,
            'improvement_percentage': improvement_percentage,
            'original_scores': original_evaluation.get('scores', {}),
            'optimized_scores': optimized_evaluation.get('scores', {})
        }

    def record_optimization(self, env_id, optimizer, trigger, original_config, optimized_config,
                            scores_before, scores_after, improvement, custom_goals=None):
        record = OptimizationRecord(
            env_id=env_id,
            optimizer=optimizer,
            trigger=trigger,
            original_config=json.dumps(original_config),
            optimized_config=json.dumps(optimized_config),
            scores_before=json.dumps(scores_before),
            scores_after=json.dumps(scores_after),
            improvement=improvement,
            custom_goals=json.dumps(custom_goals) if custom_goals else None
        )
        db.session.add(record)
        db.session.commit()
        return record.id

    def get_optimization_history(self, env_id):
        records = OptimizationRecord.query.filter_by(env_id=env_id).order_by(OptimizationRecord.created_at.desc()).all()
        return [{
            'id': rec.id,
            'optimizer': rec.optimizer,
            'trigger': rec.trigger,
            'original_config': json.loads(rec.original_config),
            'optimized_config': json.loads(rec.optimized_config),
            'scores_before': json.loads(rec.scores_before),
            'scores_after': json.loads(rec.scores_after),
            'improvement': rec.improvement,
            'custom_goals': json.loads(rec.custom_goals) if rec.custom_goals else None,
            'created_at': rec.created_at.isoformat()
        } for rec in records]

    def schedule_optimization(self, env_id, interval='daily', user_id=None, custom_goals=None):
        now = datetime.utcnow()
        if interval == 'daily':
            next_run = now + timedelta(days=1)
        elif interval == 'weekly':
            next_run = now + timedelta(weeks=1)
        elif interval == 'hourly':
            next_run = now + timedelta(hours=1)
        else:
            next_run = now + timedelta(days=1)

        existing = OptimizationSchedule.query.filter_by(env_id=env_id).first()
        if existing:
            existing.interval = interval
            existing.enabled = True
            existing.next_run = next_run
            existing.custom_goals = json.dumps(custom_goals) if custom_goals else None
            existing.created_by = user_id
            db.session.commit()
            return {
                'id': existing.id,
                'env_id': env_id,
                'interval': interval,
                'enabled': existing.enabled,
                'next_run': next_run.isoformat(),
                'custom_goals': custom_goals
            }

        schedule = OptimizationSchedule(
            env_id=env_id,
            interval=interval,
            enabled=True,
            next_run=next_run,
            custom_goals=json.dumps(custom_goals) if custom_goals else None,
            created_by=user_id
        )
        db.session.add(schedule)
        db.session.commit()

        return {
            'id': schedule.id,
            'env_id': env_id,
            'interval': interval,
            'enabled': schedule.enabled,
            'next_run': next_run.isoformat(),
            'custom_goals': custom_goals
        }

    def get_scheduled_optimizations(self):
        schedules = OptimizationSchedule.query.filter_by(enabled=True).all()
        return [{
            'id': s.id,
            'env_id': s.env_id,
            'interval': s.interval,
            'enabled': s.enabled,
            'last_run': s.last_run.isoformat() if s.last_run else None,
            'next_run': s.next_run.isoformat() if s.next_run else None,
            'custom_goals': json.loads(s.custom_goals) if s.custom_goals else None
        } for s in schedules]

    def toggle_schedule(self, schedule_id, enabled):
        schedule = OptimizationSchedule.query.get(schedule_id)
        if not schedule:
            return None
        schedule.enabled = enabled
        db.session.commit()
        return {'id': schedule.id, 'enabled': schedule.enabled}

    def run_scheduled_optimizations(self):
        now = datetime.utcnow()
        schedules = OptimizationSchedule.query.filter(
            OptimizationSchedule.enabled == True,
            OptimizationSchedule.next_run <= now
        ).all()

        results = []
        for schedule in schedules:
            env = Environment.query.get(schedule.env_id)
            if not env:
                continue

            config = json.loads(env.config)
            custom_goals = json.loads(schedule.custom_goals) if schedule.custom_goals else None

            evaluation = self.evaluate_environment(config)
            optimized_config = self.optimize_environment(config, evaluation, custom_goals)
            verification = self.verify_optimization(config, optimized_config)

            self.record_optimization(
                env_id=env.id,
                optimizer='scheduled',
                trigger='auto',
                original_config=config,
                optimized_config=optimized_config,
                scores_before=evaluation['scores'],
                scores_after=verification.get('optimized_scores', {}),
                improvement=verification.get('improvement', 0),
                custom_goals=custom_goals
            )

            env.config = json.dumps(optimized_config)
            env.status = 'optimized'

            schedule.last_run = now
            if schedule.interval == 'daily':
                schedule.next_run = now + timedelta(days=1)
            elif schedule.interval == 'weekly':
                schedule.next_run = now + timedelta(weeks=1)
            elif schedule.interval == 'hourly':
                schedule.next_run = now + timedelta(hours=1)

            results.append({'env_id': env.id, 'improvement': verification.get('improvement', 0)})

        db.session.commit()
        return results
