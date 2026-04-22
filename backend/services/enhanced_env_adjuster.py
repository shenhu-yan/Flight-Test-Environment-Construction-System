import json
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from models import db
from models.adjustment import Adjustment
from models.environment import Environment


class EnhancedEnvAdjuster:
    """
    增强版环境调整器
    支持：实时监测、多种调整策略、历史记录、批次调整
    """

    def __init__(self):
        # 调整策略映射
        self.adjustment_strategies = {
            'convergence_too_fast': self._handle_convergence_too_fast,
            'convergence_too_slow': self._handle_convergence_too_slow,
            'low_generalization': self._handle_low_generalization,
            'reward_too_low': self._handle_reward_too_low,
            'reward_too_high': self._handle_reward_too_high,
            'obstacle_concentration': self._handle_obstacle_concentration
        }

        # 调整原因说明
        self.adjustment_reasons = {
            'convergence_too_fast': '收敛速度过快，需要增加环境复杂度',
            'convergence_too_slow': '收敛速度过慢，需要简化环境',
            'low_generalization': '泛化能力不足，需要增加环境多样性',
            'reward_too_low': '奖励值过低，需要调整奖励机制',
            'reward_too_high': '奖励值过高，需要调整奖励机制',
            'obstacle_concentration': '障碍物分布不均匀'
        }

    def monitor_performance(self, env_id: str, performance_data: Dict[str, Any]) -> Tuple[bool, str, Dict[str, Any]]:
        """
        监测强化学习算法性能

        Args:
            env_id: 环境ID
            performance_data: 性能数据字典

        Returns:
            (是否需要调整, 调整原因, 详细分析)
        """
        adjustment_needed = False
        adjustment_reason = ""
        analysis = {
            'convergence_speed': performance_data.get('convergence_speed', 0.5),
            'success_rate': performance_data.get('success_rate', 0.5),
            'generalization_score': performance_data.get('generalization_score', 0.5),
            'reward_trend': performance_data.get('reward_trend', 'stable'),
            'episode_count': performance_data.get('episode_count', 0),
            'issues': []
        }

        # 检查收敛速度
        convergence_speed = analysis['convergence_speed']
        if convergence_speed > 0.9:
            adjustment_needed = True
            adjustment_reason = 'convergence_too_fast'
            analysis['issues'].append('收敛速度过快，可能导致过拟合')
        elif convergence_speed < 0.3:
            adjustment_needed = True
            adjustment_reason = 'convergence_too_slow'
            analysis['issues'].append('收敛速度过慢，需要简化环境')

        # 检查成功率
        success_rate = analysis['success_rate']
        if success_rate < 0.3:
            adjustment_needed = True
            adjustment_reason = 'convergence_too_slow'
            analysis['issues'].append('成功率过低，环境可能过于困难')
        elif success_rate > 0.95:
            adjustment_needed = True
            adjustment_reason = 'convergence_too_fast'
            analysis['issues'].append('成功率过高，环境可能过于简单')

        # 检查泛化能力
        generalization_score = analysis['generalization_score']
        if generalization_score < 0.4:
            adjustment_needed = True
            adjustment_reason = 'low_generalization'
            analysis['issues'].append('泛化能力不足，需要增加环境多样性')

        # 检查奖励趋势
        reward_trend = analysis['reward_trend']
        if reward_trend == 'decreasing':
            adjustment_needed = True
            adjustment_reason = 'reward_too_low'
            analysis['issues'].append('奖励值持续下降，需要调整奖励机制')
        elif reward_trend == 'increasing':
            adjustment_needed = True
            adjustment_reason = 'reward_too_high'
            analysis['issues'].append('奖励值持续上升，可能过于简单')

        return adjustment_needed, adjustment_reason, analysis

    def auto_adjust(self, env_config: Dict[str, Any], adjustment_reason: str,
                   performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        自动调整环境配置

        Args:
            env_config: 原始环境配置
            adjustment_reason: 调整原因
            performance_data: 性能数据

        Returns:
            调整后的环境配置
        """
        if adjustment_reason in self.adjustment_strategies:
            new_config = self.adjustment_strategies[adjustment_reason](env_config, performance_data)
            return new_config
        else:
            return env_config

    def _handle_convergence_too_fast(self, env_config: Dict[str, Any], performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理收敛速度过快的情况"""
        new_config = json.loads(json.dumps(env_config))

        # 增加障碍物
        if 'obstacles' in new_config.get('scenario', {}):
            current_obstacles = new_config['scenario']['obstacles']
            additional_obstacles = ['building', 'tree', 'lamp_post', 'wind_turbine', 'power_line']
            for obstacle in additional_obstacles:
                if obstacle not in current_obstacles:
                    current_obstacles.append(obstacle)
                    break

        # 增加天气复杂度
        weather_mapping = {
            'clear': 'windy',
            'windy': 'light_rain',
            'light_rain': 'heavy_rain',
            'heavy_rain': 'storm'
        }
        current_weather = new_config.get('scenario', {}).get('weather', 'clear')
        if current_weather in weather_mapping:
            new_config['scenario']['weather'] = weather_mapping[current_weather]

        # 降低奖励值
        if 'reward' in new_config:
            current_reward = new_config['reward'].get('reward_value', 10)
            new_config['reward']['reward_value'] = max(1, int(current_reward * 0.8))

        # 增加惩罚项
        if 'reward' in new_config:
            penalty_rules = new_config['reward'].get('penalty_rules', [])
            additional_penalties = ['timeout', 'imbalance', 'energy_waste']
            for penalty in additional_penalties:
                if penalty not in penalty_rules:
                    penalty_rules.append(penalty)
                    break
            new_config['reward']['penalty_rules'] = penalty_rules

        return new_config

    def _handle_convergence_too_slow(self, env_config: Dict[str, Any], performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理收敛速度过慢的情况"""
        new_config = json.loads(json.dumps(env_config))

        # 减少障碍物
        if 'obstacles' in new_config.get('scenario', {}) and len(new_config['scenario']['obstacles']) > 0:
            new_config['scenario']['obstacles'] = new_config['scenario']['obstacles'][:-1]

        # 降低天气复杂度
        weather_mapping = {
            'storm': 'heavy_rain',
            'heavy_rain': 'light_rain',
            'light_rain': 'windy',
            'windy': 'clear'
        }
        current_weather = new_config.get('scenario', {}).get('weather', 'clear')
        if current_weather in weather_mapping:
            new_config['scenario']['weather'] = weather_mapping[current_weather]

        # 提高奖励值
        if 'reward' in new_config:
            current_reward = new_config['reward'].get('reward_value', 10)
            new_config['reward']['reward_value'] = int(current_reward * 1.2)

        # 简化惩罚项
        if 'reward' in new_config:
            penalty_rules = new_config['reward'].get('penalty_rules', [])
            if 'timeout' in penalty_rules:
                penalty_rules.remove('timeout')
            if 'imbalance' in penalty_rules:
                penalty_rules.remove('imbalance')
            new_config['reward']['penalty_rules'] = penalty_rules

        return new_config

    def _handle_low_generalization(self, env_config: Dict[str, Any], performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理泛化能力不足的情况"""
        new_config = json.loads(json.dumps(env_config))

        # 随机化天气
        weather_options = ['clear', 'windy', 'light_rain', 'heavy_rain', 'storm']
        new_config['scenario']['weather'] = random.choice(weather_options)

        # 增加障碍物多样性
        obstacle_options = ['building', 'tree', 'lamp_post', 'wind_turbine', 'power_line', 'bird']
        if 'obstacles' in new_config.get('scenario', {}):
            current_obstacles = new_config['scenario']['obstacles']
            available_obstacles = [obs for obs in obstacle_options if obs not in current_obstacles]
            if available_obstacles and len(current_obstacles) < 4:
                current_obstacles.append(random.choice(available_obstacles))

        return new_config

    def _handle_reward_too_low(self, env_config: Dict[str, Any], performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理奖励值过低的情况"""
        new_config = json.loads(json.dumps(env_config))

        if 'reward' in new_config:
            current_reward = new_config['reward'].get('reward_value', 10)
            new_config['reward']['reward_value'] = int(current_reward * 1.3)

            # 降低惩罚强度
            penalty_rules = new_config['reward'].get('penalty_rules', [])
            if 'collision' in penalty_rules:
                penalty_rules.remove('collision')
            new_config['reward']['penalty_rules'] = penalty_rules

        return new_config

    def _handle_reward_too_high(self, env_config: Dict[str, Any], performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理奖励值过高的情况"""
        new_config = json.loads(json.dumps(env_config))

        if 'reward' in new_config:
            current_reward = new_config['reward'].get('reward_value', 10)
            new_config['reward']['reward_value'] = max(1, int(current_reward * 0.8))

            # 增加惩罚项
            penalty_rules = new_config['reward'].get('penalty_rules', [])
            if 'timeout' not in penalty_rules:
                penalty_rules.append('timeout')
            new_config['reward']['penalty_rules'] = penalty_rules

        return new_config

    def _handle_obstacle_concentration(self, env_config: Dict[str, Any], performance_data: Dict[str, Any]) -> Dict[str, Any]:
        """处理障碍物分布不均的情况"""
        new_config = json.loads(json.dumps(env_config))

        # 随机更新障碍物列表
        obstacle_options = ['building', 'tree', 'lamp_post', 'wind_turbine', 'power_line', 'bird']
        if 'obstacles' in new_config.get('scenario', {}):
            current_obstacles = new_config['scenario']['obstacles']
            if len(current_obstacles) > 0:
                # 替换部分障碍物
                num_to_replace = max(1, len(current_obstacles) // 2)
                for i in range(min(num_to_replace, len(current_obstacles))):
                    new_obs = random.choice([o for o in obstacle_options if o not in current_obstacles])
                    if new_obs:
                        current_obstacles[i] = new_obs
            else:
                # 添加障碍物
                current_obstacles.append(random.choice(obstacle_options))

        return new_config

    def manual_adjust(self, env_config: Dict[str, Any], adjustment_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        手动调整环境配置

        Args:
            env_config: 原始环境配置
            adjustment_params: 调整参数

        Returns:
            调整后的环境配置
        """
        new_config = json.loads(json.dumps(env_config))

        def update_config(config: Dict[str, Any], params: Dict[str, Any]) -> None:
            for key, value in params.items():
                if isinstance(value, dict) and key in config and isinstance(config[key], dict):
                    update_config(config[key], value)
                else:
                    config[key] = value

        update_config(new_config, adjustment_params)
        return new_config

    def batch_adjust(self, env_configs: List[Dict[str, Any]], adjustment_reason: str,
                    performance_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量调整环境配置

        Args:
            env_configs: 环境配置列表
            adjustment_reason: 调整原因
            performance_data_list: 性能数据列表

        Returns:
            调整后的环境配置列表
        """
        adjusted_configs = []
        for env_config, performance_data in zip(env_configs, performance_data_list):
            adjusted_config = self.auto_adjust(env_config, adjustment_reason, performance_data)
            adjusted_configs.append(adjusted_config)
        return adjusted_configs

    def record_adjustment(self, env_id: str, adjuster: str, trigger: str, params: Dict[str, Any],
                         reason: str, performance_before: Optional[Dict[str, Any]] = None,
                         performance_after: Optional[Dict[str, Any]] = None) -> int:
        """
        记录调整历史

        Args:
            env_id: 环境ID
            adjuster: 调整者
            trigger: 触发方式（auto/manual）
            params: 调整参数
            reason: 调整原因
            performance_before: 调整前性能
            performance_after: 调整后性能

        Returns:
            记录ID
        """
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

    def rollback_adjustment(self, env_id: str, adjustment_id: int) -> Optional[Dict[str, Any]]:
        """
        回滚到指定调整

        Args:
            env_id: 环境ID
            adjustment_id: 调整记录ID

        Returns:
            回滚后的环境信息，如果失败返回None
        """
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

        return {
            'id': env.id,
            'env_id': env.env_id,
            'env_name': env.env_name,
            'config': old_params
        }

    def get_adjustment_history(self, env_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        获取环境调整历史

        Args:
            env_id: 环境ID
            limit: 返回记录数量限制

        Returns:
            调整历史列表
        """
        adjustments = Adjustment.query.filter_by(env_id=env_id).order_by(Adjustment.created_at.desc()).limit(limit).all()
        return [{
            'id': adj.id,
            'adjuster': adj.adjuster,
            'trigger': adj.trigger,
            'params': json.loads(adj.params),
            'reason': adj.reason,
            'reason_text': self.adjustment_reasons.get(adj.reason, adj.reason),
            'performance_before': json.loads(adj.performance_before) if adj.performance_before else None,
            'performance_after': json.loads(adj.performance_after) if adj.performance_after else None,
            'created_at': adj.created_at.isoformat()
        } for adj in adjustments]

    def get_performance_trend(self, env_id: str, days: int = 7) -> Dict[str, Any]:
        """
        获取性能趋势分析

        Args:
            env_id: 环境ID
            days: 分析天数

        Returns:
            趋势分析结果
        """
        from datetime import datetime, timedelta
        start_date = datetime.utcnow() - timedelta(days=days)

        adjustments = Adjustment.query.filter(
            Adjustment.env_id == env_id,
            Adjustment.created_at >= start_date
        ).order_by(Adjustment.created_at.asc()).all()

        if not adjustments:
            return {'trend': 'stable', 'changes': 0, 'analysis': '无调整历史'}

        # 分析调整频率和原因
        total_adjustments = len(adjustments)
        adjustment_reasons = {}
        for adj in adjustments:
            reason = adj.reason
            adjustment_reasons[reason] = adjustment_reasons.get(reason, 0) + 1

        # 确定趋势
        if total_adjustments > 3:
            trend = 'frequent' if total_adjustments > 5 else 'moderate'
        else:
            trend = 'stable'

        return {
            'trend': trend,
            'changes': total_adjustments,
            'reason_distribution': adjustment_reasons,
            'analysis': f'过去{days}天内共进行了{total_adjustments}次调整，主要原因为：{", ".join(adjustment_reasons.keys())}'
        }
