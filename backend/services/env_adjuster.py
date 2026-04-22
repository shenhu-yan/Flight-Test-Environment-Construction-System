import json
import random
from datetime import datetime
from models import db
from models.adjustment import Adjustment
from models.environment import Environment


class EnvAdjuster:
    def __init__(self):
        self.adjustment_strategies = {
            'convergence_too_fast': self._handle_convergence_too_fast,
            'convergence_too_slow': self._handle_convergence_too_slow,
            'low_generalization': self._handle_low_generalization
        }

    def monitor_performance(self, env_id, performance_data):
        adjustment_needed = False
        adjustment_reason = ""

        if performance_data.get('convergence_speed', 0) > 0.9:
            adjustment_needed = True
            adjustment_reason = 'convergence_too_fast'
        elif performance_data.get('convergence_speed', 0) < 0.3:
            adjustment_needed = True
            adjustment_reason = 'convergence_too_slow'

        if performance_data.get('success_rate', 0) < 0.5:
            adjustment_needed = True
            adjustment_reason = 'convergence_too_slow'

        if performance_data.get('generalization_score', 0) < 0.4:
            adjustment_needed = True
            adjustment_reason = 'low_generalization'

        return adjustment_needed, adjustment_reason

    def auto_adjust(self, env_config, adjustment_reason, performance_data):
        if adjustment_reason in self.adjustment_strategies:
            new_config = self.adjustment_strategies[adjustment_reason](env_config, performance_data)
            return new_config
        else:
            return env_config

    def _handle_convergence_too_fast(self, env_config, performance_data):
        new_config = json.loads(json.dumps(env_config))

        if 'obstacles' in new_config.get('scenario', {}):
            current_obstacles = new_config['scenario']['obstacles']
            additional_obstacles = ['building', 'tree', 'lamp_post', 'wind_turbine']
            for obstacle in additional_obstacles:
                if obstacle not in current_obstacles:
                    current_obstacles.append(obstacle)
                    break

        weather_mapping = {
            'clear': 'windy', 'windy': 'light_rain',
            'light_rain': 'heavy_rain', 'heavy_rain': 'storm'
        }
        current_weather = new_config.get('scenario', {}).get('weather', 'clear')
        if current_weather in weather_mapping:
            new_config['scenario']['weather'] = weather_mapping[current_weather]

        if 'reward' in new_config:
            current_reward = new_config['reward'].get('reward_value', 10)
            new_config['reward']['reward_value'] = max(1, current_reward * 0.8)

        return new_config

    def _handle_convergence_too_slow(self, env_config, performance_data):
        new_config = json.loads(json.dumps(env_config))

        if 'obstacles' in new_config.get('scenario', {}) and len(new_config['scenario']['obstacles']) > 0:
            new_config['scenario']['obstacles'] = new_config['scenario']['obstacles'][:-1]

        weather_mapping = {
            'storm': 'heavy_rain', 'heavy_rain': 'light_rain',
            'light_rain': 'windy', 'windy': 'clear'
        }
        current_weather = new_config.get('scenario', {}).get('weather', 'clear')
        if current_weather in weather_mapping:
            new_config['scenario']['weather'] = weather_mapping[current_weather]

        if 'reward' in new_config:
            current_reward = new_config['reward'].get('reward_value', 10)
            new_config['reward']['reward_value'] = current_reward * 1.2

        return new_config

    def _handle_low_generalization(self, env_config, performance_data):
        new_config = json.loads(json.dumps(env_config))

        weather_options = ['clear', 'windy', 'light_rain', 'heavy_rain', 'storm']
        new_config['scenario']['weather'] = random.choice(weather_options)

        obstacle_options = ['building', 'tree', 'lamp_post', 'wind_turbine', 'power_line']
        if 'obstacles' in new_config.get('scenario', {}):
            current_obstacles = new_config['scenario']['obstacles']
            available_obstacles = [obs for obs in obstacle_options if obs not in current_obstacles]
            if available_obstacles:
                current_obstacles.append(random.choice(available_obstacles))

        return new_config

    def manual_adjust(self, env_config, adjustment_params):
        new_config = json.loads(json.dumps(env_config))

        def update_config(config, params):
            for key, value in params.items():
                if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                    update_config(config[key], value)
                else:
                    config[key] = value

        update_config(new_config, adjustment_params)
        return new_config

    def record_adjustment(self, env_id, adjuster, trigger, params, reason, performance_before=None, performance_after=None):
        adjustment = Adjustment(
            env_id=env_id,
            adjuster=adjuster,
            trigger=trigger,
            params=json.dumps(params),
            reason=reason,
            performance_before=json.dumps(performance_before) if performance_before else None,
            performance_after=json.dumps(performance_after) if performance_after else None
        )
        db.session.add(adjustment)
        db.session.commit()
        return adjustment.id

    def rollback_adjustment(self, env_id, adjustment_id):
        adjustment = Adjustment.query.get(adjustment_id)
        if not adjustment or adjustment.env_id != env_id:
            return None

        env = Environment.query.get(env_id)
        if not env:
            return None

        old_params = json.loads(adjustment.params)
        env.config = json.dumps(old_params)
        env.status = 'adjusted'
        db.session.commit()
        return env

    def get_adjustment_history(self, env_id):
        adjustments = Adjustment.query.filter_by(env_id=env_id).order_by(Adjustment.created_at.desc()).all()
        return [{
            'id': adj.id,
            'adjuster': adj.adjuster,
            'trigger': adj.trigger,
            'params': json.loads(adj.params),
            'reason': adj.reason,
            'performance_before': json.loads(adj.performance_before) if adj.performance_before else None,
            'performance_after': json.loads(adj.performance_after) if adj.performance_after else None,
            'created_at': adj.created_at.isoformat()
        } for adj in adjustments]
