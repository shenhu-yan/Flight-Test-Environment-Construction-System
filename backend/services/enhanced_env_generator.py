import json
import xml.etree.ElementTree as ET
import uuid
import random
from datetime import datetime
from typing import List, Dict, Any, Optional


class EnhancedEnvGenerator:
    """
    增强版环境生成器
    支持：模板库、批量生成、多种描述语言、复杂度控制
    """

    def __init__(self):
        # 地形类型配置
        self.terrain_types = {
            'flat': {'name': '平坦地形', 'complexity': 1, 'difficulty': 1.0},
            'hilly': {'name': '丘陵地形', 'complexity': 2, 'difficulty': 1.5},
            'mountainous': {'name': '山地地形', 'complexity': 4, 'difficulty': 2.5},
            'urban': {'name': '城市地形', 'complexity': 3, 'difficulty': 2.0},
            'forest': {'name': '森林地形', 'complexity': 2, 'difficulty': 1.8}
        }

        # 天气类型配置
        self.weather_types = {
            'clear': {'name': '晴朗', 'complexity': 1, 'difficulty': 1.0},
            'windy': {'name': '有风', 'complexity': 2, 'difficulty': 1.3},
            'light_rain': {'name': '小雨', 'complexity': 2, 'difficulty': 1.5},
            'heavy_rain': {'name': '大雨', 'complexity': 3, 'difficulty': 2.0},
            'storm': {'name': '风暴', 'complexity': 4, 'difficulty': 2.5}
        }

        # 障碍物类型配置
        self.obstacle_types = {
            'building': {'name': '建筑物', 'complexity': 2, 'difficulty': 2.0},
            'tree': {'name': '树木', 'complexity': 1, 'difficulty': 1.2},
            'lamp_post': {'name': '路灯', 'complexity': 1, 'difficulty': 1.1},
            'wind_turbine': {'name': '风力发电机', 'complexity': 3, 'difficulty': 2.2},
            'power_line': {'name': '电线', 'complexity': 2, 'difficulty': 1.8},
            'bird': {'name': '鸟类', 'complexity': 2, 'difficulty': 1.5}
        }

        # 飞行动力学配置
        self.dynamics_types = {
            'basic': {'name': '基础', 'complexity': 1, 'realism': 1.0},
            'medium': {'name': '中等', 'complexity': 2, 'realism': 2.0},
            'advanced': {'name': '高级', 'complexity': 4, 'realism': 3.0}
        }

        # 空气动力学配置
        self.aero_types = {
            'basic': {'name': '基础', 'complexity': 1, 'realism': 1.0},
            'medium': {'name': '中等', 'complexity': 2, 'realism': 2.0},
            'detailed': {'name': '详细', 'complexity': 3, 'realism': 3.0},
            'precise': {'name': '精确', 'complexity': 4, 'realism': 3.5}
        }

        # 环境模板库
        self.template_library = self._init_template_library()

    def _init_template_library(self) -> Dict[str, Dict[str, Any]]:
        """初始化环境模板库"""
        return {
            'drone_basic': {
                'id': 'TPL_DRONE_BASIC',
                'name': '无人机基础测试环境',
                'type': 'drone',
                'complexity': 'low',
                'test_type': 'basic_control',
                'description': '适用于无人机基础控制算法测试的简单环境',
                'config': {
                    'scenario': {
                        'terrain': 'flat',
                        'weather': 'clear',
                        'obstacles': []
                    },
                    'physics': {
                        'flight_dynamics': 'basic',
                        'aerodynamics': 'basic',
                        'collision_detection': 'enabled'
                    },
                    'reward': {
                        'reward_value': 10,
                        'penalty_rules': ['collision', 'out_of_bounds'],
                        'target_threshold': 0.1
                    }
                }
            },
            'drone_medium': {
                'id': 'TPL_DRONE_MEDIUM',
                'name': '无人机中等复杂度环境',
                'type': 'drone',
                'complexity': 'medium',
                'test_type': 'environment_adaptation',
                'description': '适用于无人机环境适应性测试的中等难度环境',
                'config': {
                    'scenario': {
                        'terrain': 'urban',
                        'weather': 'light_rain',
                        'obstacles': ['building', 'lamp_post']
                    },
                    'physics': {
                        'flight_dynamics': 'medium',
                        'aerodynamics': 'medium',
                        'collision_detection': 'enabled'
                    },
                    'reward': {
                        'reward_value': 15,
                        'penalty_rules': ['collision', 'out_of_bounds'],
                        'target_threshold': 0.08
                    }
                }
            },
            'drone_advanced': {
                'id': 'TPL_DRONE_ADVANCED',
                'name': '无人机高级测试环境',
                'type': 'drone',
                'complexity': 'high',
                'test_type': 'obstacle_avoidance',
                'description': '适用于无人机高级避障算法测试的复杂环境',
                'config': {
                    'scenario': {
                        'terrain': 'mountainous',
                        'weather': 'storm',
                        'obstacles': ['building', 'tree', 'wind_turbine', 'power_line']
                    },
                    'physics': {
                        'flight_dynamics': 'advanced',
                        'aerodynamics': 'detailed',
                        'collision_detection': 'enabled'
                    },
                    'reward': {
                        'reward_value': 20,
                        'penalty_rules': ['collision', 'out_of_bounds', 'timeout'],
                        'target_threshold': 0.05
                    }
                }
            },
            'fixed_wing_basic': {
                'id': 'TPL_FIXED_WING_BASIC',
                'name': '固定翼基础测试环境',
                'type': 'fixed_wing',
                'complexity': 'low',
                'test_type': 'basic_control',
                'description': '适用于固定翼飞机基础控制算法测试的简单环境',
                'config': {
                    'scenario': {
                        'terrain': 'flat',
                        'weather': 'clear',
                        'obstacles': []
                    },
                    'physics': {
                        'flight_dynamics': 'medium',
                        'aerodynamics': 'detailed',
                        'collision_detection': 'enabled'
                    },
                    'reward': {
                        'reward_value': 12,
                        'penalty_rules': ['collision', 'out_of_bounds'],
                        'target_threshold': 0.08
                    }
                }
            },
            'rotor_advanced': {
                'id': 'TPL_ROTOR_ADVANCED',
                'name': '旋翼机高级测试环境',
                'type': 'rotor',
                'complexity': 'high',
                'test_type': 'precision_landing',
                'description': '适用于旋翼机精确着陆算法测试的复杂环境',
                'config': {
                    'scenario': {
                        'terrain': 'hilly',
                        'weather': 'windy',
                        'obstacles': ['tree', 'lamp_post']
                    },
                    'physics': {
                        'flight_dynamics': 'advanced',
                        'aerodynamics': 'precise',
                        'collision_detection': 'enabled'
                    },
                    'reward': {
                        'reward_value': 25,
                        'penalty_rules': ['collision', 'out_of_bounds', 'imbalance'],
                        'target_threshold': 0.03
                    }
                }
            }
        }

    def get_template_library(self, filters: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
        """
        获取模板库，支持过滤

        Args:
            filters: 过滤条件，如 {'type': 'drone', 'complexity': 'medium'}

        Returns:
            模板列表
        """
        templates = list(self.template_library.values())

        if filters:
            for key, value in filters.items():
                if key == 'type':
                    templates = [t for t in templates if t.get('type') == value]
                elif key == 'complexity':
                    templates = [t for t in templates if t.get('complexity') == value]
                elif key == 'test_type':
                    templates = [t for t in templates if t.get('test_type') == value]

        return templates

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        获取单个模板

        Args:
            template_id: 模板ID

        Returns:
            模板信息，如果不存在返回None
        """
        for template in self.template_library.values():
            if template['id'] == template_id:
                return template.copy()
        return None

    def parse_config(self, config_content: Any, config_format: str = 'json') -> Dict[str, Any]:
        """
        解析环境配置文件

        Args:
            config_content: 配置内容（字符串或字典）
            config_format: 配置格式，支持 'json' 或 'xml'

        Returns:
            解析后的配置字典
        """
        if config_format == 'json':
            if isinstance(config_content, str):
                return json.loads(config_content)
            return config_content
        elif config_format == 'xml':
            if isinstance(config_content, str):
                root = ET.fromstring(config_content)
            else:
                root = config_content
            return self._parse_xml_config(root)
        else:
            raise ValueError(f'Unsupported config format: {config_format}')

    def _parse_xml_config(self, root: ET.Element) -> Dict[str, Any]:
        """解析XML配置"""
        config = {}
        for child in root:
            if child.tag == 'scenario':
                config['scenario'] = {}
                for sc in child:
                    if sc.tag == 'obstacles':
                        config['scenario']['obstacles'] = [item.text for item in sc]
                    else:
                        config['scenario'][sc.tag] = sc.text
            elif child.tag == 'physics':
                config['physics'] = {}
                for pc in child:
                    config['physics'][pc.tag] = pc.text
            elif child.tag == 'reward':
                config['reward'] = {}
                for rc in child:
                    if rc.tag == 'penalty_rules':
                        config['reward']['penalty_rules'] = [item.text for item in rc]
                    else:
                        config['reward'][rc.tag] = float(rc.text) if rc.text and rc.tag != 'penalty_rules' else rc.text
        return config

    def config_to_xml(self, config: Dict[str, Any]) -> str:
        """
        将配置转换为XML格式

        Args:
            config: 配置字典

        Returns:
            XML字符串
        """
        root = ET.Element('environment')

        # 场景配置
        scenario_el = ET.SubElement(root, 'scenario')
        for key, val in config.get('scenario', {}).items():
            if key == 'obstacles':
                obs_el = ET.SubElement(scenario_el, 'obstacles')
                for obs in val:
                    item = ET.SubElement(obs_el, 'item')
                    item.text = obs
            else:
                el = ET.SubElement(scenario_el, key)
                el.text = str(val)

        # 物理配置
        physics_el = ET.SubElement(root, 'physics')
        for key, val in config.get('physics', {}).items():
            el = ET.SubElement(physics_el, key)
            el.text = str(val)

        # 奖励配置
        reward_el = ET.SubElement(root, 'reward')
        for key, val in config.get('reward', {}).items():
            if key == 'penalty_rules':
                pr_el = ET.SubElement(reward_el, 'penalty_rules')
                for rule in val:
                    item = ET.SubElement(pr_el, 'item')
                    item.text = rule
            else:
                el = ET.SubElement(reward_el, key)
                el.text = str(val)

        return ET.tostring(root, encoding='unicode')

    def generate_preview(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        生成环境预览信息

        Args:
            config: 环境配置

        Returns:
            预览信息字典
        """
        scenario = config.get('scenario', {})
        physics = config.get('physics', {})
        reward = config.get('reward', {})

        # 构建预览数据
        preview = {
            'summary': {
                'terrain': self.terrain_types.get(scenario.get('terrain', ''), {}).get('name', scenario.get('terrain', '')),
                'weather': self.weather_types.get(scenario.get('weather', ''), {}).get('name', scenario.get('weather', '')),
                'obstacle_count': len(scenario.get('obstacles', [])),
                'obstacle_names': [
                    self.obstacle_types.get(o, {}).get('name', o)
                    for o in scenario.get('obstacles', [])
                ],
                'flight_dynamics': self.dynamics_types.get(physics.get('flight_dynamics', ''), {}).get('name', physics.get('flight_dynamics', '')),
                'aerodynamics': self.aero_types.get(physics.get('aerodynamics', ''), {}).get('name', physics.get('aerodynamics', '')),
                'reward_value': reward.get('reward_value', 10),
                'penalty_count': len(reward.get('penalty_rules', [])),
                'target_threshold': reward.get('target_threshold', 0.1)
            },
            'complexity_score': self._calc_complexity(config),
            'scene_description': self._generate_scene_description(config),
            'metrics': self._calculate_metrics(config)
        }
        return preview

    def _calc_complexity(self, config: Dict[str, Any]) -> float:
        """计算环境复杂度评分"""
        score = 0
        scenario = config.get('scenario', {})
        terrain = scenario.get('terrain', 'flat')
        weather = scenario.get('weather', 'clear')
        obstacles = scenario.get('obstacles', [])

        # 获取各类别的复杂度值
        terrain_complexity = self.terrain_types.get(terrain, {}).get('complexity', 1)
        weather_complexity = self.weather_types.get(weather, {}).get('complexity', 1)
        obstacle_complexity = sum(
            self.obstacle_types.get(obs, {}).get('complexity', 1)
            for obs in obstacles
        ) / max(len(obstacles), 1)

        # 物理模型复杂度
        physics = config.get('physics', {})
        dynamics = physics.get('flight_dynamics', 'basic')
        aero = physics.get('aerodynamics', 'basic')
        dynamics_complexity = self.dynamics_types.get(dynamics, {}).get('complexity', 1)
        aero_complexity = self.aero_types.get(aero, {}).get('complexity', 1)

        # 综合评分
        total_score = (terrain_complexity + weather_complexity + obstacle_complexity +
                      dynamics_complexity + aero_complexity) / 5.0

        return round(total_score, 2)

    def _generate_scene_description(self, config: Dict[str, Any]) -> str:
        """生成场景描述文字"""
        scenario = config.get('scenario', {})
        terrain = self.terrain_types.get(scenario.get('terrain', ''), {}).get('name', '未知地形')
        weather = self.weather_types.get(scenario.get('weather', ''), {}).get('name', '未知天气')
        obstacles = scenario.get('obstacles', [])
        obs_names = [
            self.obstacle_types.get(o, {}).get('name', o)
            for o in obstacles
        ]

        desc = f"在{terrain}上，天气{weather}"
        if obs_names:
            desc += f"，存在{', '.join(obs_names)}等障碍物"
        return desc

    def _calculate_metrics(self, config: Dict[str, Any]) -> Dict[str, float]:
        """计算环境各项指标"""
        scenario = config.get('scenario', {})
        physics = config.get('physics', {})
        reward = config.get('reward', {})

        # 多样性指标
        terrain_diversity = len(self.terrain_types) / 5.0
        weather_diversity = len(self.weather_types) / 5.0
        diversity_score = (terrain_diversity + weather_diversity) / 2.0

        # 挑战性指标
        weather = scenario.get('weather', 'clear')
        obstacles = scenario.get('obstacles', [])
        weather_difficulty = self.weather_types.get(weather, {}).get('difficulty', 1.0)
        obstacle_difficulty = min(len(obstacles) / 4.0, 1.0)
        challenge_score = (weather_difficulty + obstacle_difficulty) / 2.0

        # 真实性指标
        dynamics_realism = self.dynamics_types.get(physics.get('flight_dynamics', 'basic'), {}).get('realism', 1.0)
        aero_realism = self.aero_types.get(physics.get('aerodynamics', 'basic'), {}).get('realism', 1.0)
        realism_score = (dynamics_realism + aero_realism) / 3.5

        return {
            'diversity': round(diversity_score, 2),
            'challenge': round(challenge_score, 2),
            'realism': round(realism_score, 2)
        }

    def _generate_scene_description(self, config: Dict[str, Any]) -> str:
        """生成场景描述文字"""
        scenario = config.get('scenario', {})
        terrain = self.terrain_types.get(scenario.get('terrain', ''), {}).get('name', '未知地形')
        weather = self.weather_types.get(scenario.get('weather', ''), {}).get('name', '未知天气')
        obstacles = scenario.get('obstacles', [])
        obs_names = [
            self.obstacle_types.get(o, {}).get('name', o)
            for o in obstacles
        ]

        desc = f"在{terrain}上，天气{weather}"
        if obs_names:
            desc += f"，存在{', '.join(obs_names)}等障碍物"
        return desc

    def generate_environment(self, config: Dict[str, Any], batch_count: int = 1) -> List[Dict[str, Any]]:
        """
        生成环境实例

        Args:
            config: 环境配置
            batch_count: 批量生成数量

        Returns:
            环境实例列表
        """
        environments = []
        for i in range(batch_count):
            env_id = f"ENV_{uuid.uuid4().hex[:8]}"
            preview = self.generate_preview(config)
            env = {
                'env_id': env_id,
                'config': config,
                'preview_data': preview,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'created'
            }
            environments.append(env)
        return environments

    def generate_from_template(self, template_id: str, variations: int = 1) -> List[Dict[str, Any]]:
        """
        基于模板生成环境

        Args:
            template_id: 模板ID
            variations: 生成变体数量

        Returns:
            环境实例列表
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f'Template {template_id} not found')

        environments = []
        base_config = template['config']

        for i in range(variations):
            # 创建变体配置
            config = self._create_config_variant(base_config)
            env_id = f"ENV_{uuid.uuid4().hex[:8]}"
            preview = self.generate_preview(config)

            env = {
                'env_id': env_id,
                'template_id': template_id,
                'config': config,
                'preview_data': preview,
                'created_at': datetime.utcnow().isoformat(),
                'status': 'created'
            }
            environments.append(env)

        return environments

    def _create_config_variant(self, base_config: Dict[str, Any]) -> Dict[str, Any]:
        """创建配置变体"""
        import copy
        config = copy.deepcopy(base_config)

        # 随机调整地形
        terrain_options = list(self.terrain_types.keys())
        config['scenario']['terrain'] = random.choice(terrain_options)

        # 随机调整天气
        weather_options = list(self.weather_types.keys())
        config['scenario']['weather'] = random.choice(weather_options)

        # 随机调整障碍物
        obstacle_options = list(self.obstacle_types.keys())
        current_obstacles = config['scenario'].get('obstacles', [])
        if random.random() > 0.5 and current_obstacles:
            # 添加新障碍物
            available = [o for o in obstacle_options if o not in current_obstacles]
            if available:
                current_obstacles.append(random.choice(available))
        config['scenario']['obstacles'] = current_obstacles

        return config

    def export_environment(self, env_id: str, config: Dict[str, Any], fmt: str = 'json') -> str:
        """
        导出环境配置

        Args:
            env_id: 环境ID
            config: 环境配置
            fmt: 导出格式

        Returns:
            导出文件路径
        """
        export_dir = 'exports/environments'
        import os
        os.makedirs(export_dir, exist_ok=True)

        if fmt == 'xml':
            content = self.config_to_xml(config)
            export_path = os.path.join(export_dir, f'{env_id}.xml')
        else:
            content = json.dumps(config, ensure_ascii=False, indent=2)
            export_path = os.path.join(export_dir, f'{env_id}.json')

        with open(export_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return export_path

    def import_environment(self, import_file: str, fmt: str = 'json') -> Dict[str, Any]:
        """
        导入环境配置

        Args:
            import_file: 导入文件路径
            fmt: 文件格式

        Returns:
            导入的配置字典
        """
        with open(import_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_config(content, fmt)

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, list[str]]:
        """
        验证环境配置的有效性

        Args:
            config: 环境配置

        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []

        # 检查必需的顶级字段
        required_fields = ['scenario', 'physics', 'reward']
        for field in required_fields:
            if field not in config:
                errors.append(f"缺少必需字段: {field}")

        # 检查场景配置
        if 'scenario' in config:
            scenario = config['scenario']
            if 'terrain' not in scenario:
                errors.append("场景配置缺少 'terrain' 字段")
            elif scenario['terrain'] not in self.terrain_types:
                errors.append(f"未知的地形类型: {scenario['terrain']}")

            if 'weather' not in scenario:
                errors.append("场景配置缺少 'weather' 字段")
            elif scenario['weather'] not in self.weather_types:
                errors.append(f"未知的天气类型: {scenario['weather']}")

        # 检查物理配置
        if 'physics' in config:
            physics = config['physics']
            if 'flight_dynamics' in physics and physics['flight_dynamics'] not in self.dynamics_types:
                errors.append(f"未知的飞行动力学类型: {physics['flight_dynamics']}")

            if 'aerodynamics' in physics and physics['aerodynamics'] not in self.aero_types:
                errors.append(f"未知的空气动力学类型: {physics['aerodynamics']}")

        return len(errors) == 0, errors
