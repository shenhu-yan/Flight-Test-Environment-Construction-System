import json
import xml.etree.ElementTree as ET
import uuid
from datetime import datetime


class EnvGenerator:
    def __init__(self):
        pass

    def parse_config(self, config_content, config_format='json'):
        if config_format == 'json':
            if isinstance(config_content, str):
                return json.loads(config_content)
            return config_content
        elif config_format == 'xml':
            if isinstance(config_content, str):
                root = ET.fromstring(config_content)
            else:
                root = config_content
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
        else:
            raise ValueError(f'Unsupported config format: {config_format}')

    def config_to_xml(self, config):
        root = ET.Element('environment')
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

        physics_el = ET.SubElement(root, 'physics')
        for key, val in config.get('physics', {}).items():
            el = ET.SubElement(physics_el, key)
            el.text = str(val)

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

    def generate_preview(self, config):
        scenario = config.get('scenario', {})
        physics = config.get('physics', {})
        reward = config.get('reward', {})

        terrain_labels = {
            'flat': '平坦地形', 'hilly': '丘陵地形', 'mountainous': '山地地形',
            'urban': '城市地形', 'forest': '森林地形'
        }
        weather_labels = {
            'clear': '晴朗', 'windy': '有风', 'light_rain': '小雨',
            'heavy_rain': '大雨', 'storm': '风暴'
        }
        obstacle_labels = {
            'building': '建筑物', 'tree': '树木', 'lamp_post': '路灯',
            'wind_turbine': '风力发电机', 'power_line': '电线', 'bird': '鸟类'
        }
        dynamics_labels = {
            'basic': '基础', 'medium': '中等', 'advanced': '高级'
        }
        aero_labels = {
            'basic': '基础', 'medium': '中等', 'detailed': '详细', 'precise': '精确'
        }

        preview = {
            'summary': {
                'terrain': terrain_labels.get(scenario.get('terrain', ''), scenario.get('terrain', '')),
                'weather': weather_labels.get(scenario.get('weather', ''), scenario.get('weather', '')),
                'obstacle_count': len(scenario.get('obstacles', [])),
                'obstacle_names': [obstacle_labels.get(o, o) for o in scenario.get('obstacles', [])],
                'flight_dynamics': dynamics_labels.get(physics.get('flight_dynamics', ''), physics.get('flight_dynamics', '')),
                'aerodynamics': aero_labels.get(physics.get('aerodynamics', ''), physics.get('aerodynamics', '')),
                'reward_value': reward.get('reward_value', 10),
                'penalty_count': len(reward.get('penalty_rules', [])),
                'target_threshold': reward.get('target_threshold', 0.1)
            },
            'complexity_score': self._calc_complexity(config),
            'scene_description': self._generate_scene_description(config)
        }
        return preview

    def _calc_complexity(self, config):
        score = 0
        scenario = config.get('scenario', {})
        terrain = scenario.get('terrain', 'flat')
        weather = scenario.get('weather', 'clear')
        obstacles = scenario.get('obstacles', [])
        physics = config.get('physics', {})
        dynamics = physics.get('flight_dynamics', 'basic')

        terrain_scores = {'flat': 1, 'hilly': 2, 'mountainous': 4, 'urban': 3, 'forest': 2}
        weather_scores = {'clear': 1, 'windy': 2, 'light_rain': 3, 'heavy_rain': 4, 'storm': 5}
        dynamics_scores = {'basic': 1, 'medium': 2, 'advanced': 4}

        score += terrain_scores.get(terrain, 1)
        score += weather_scores.get(weather, 1)
        score += min(len(obstacles), 5)
        score += dynamics_scores.get(dynamics, 1)
        max_score = 4 + 5 + 5 + 4
        return round(score / max_score, 2)

    def _generate_scene_description(self, config):
        scenario = config.get('scenario', {})
        terrain_map = {'flat': '平坦', 'hilly': '丘陵', 'mountainous': '山地', 'urban': '城市', 'forest': '森林'}
        weather_map = {'clear': '晴朗', 'windy': '有风', 'light_rain': '小雨', 'heavy_rain': '大雨', 'storm': '风暴'}
        terrain = terrain_map.get(scenario.get('terrain', ''), scenario.get('terrain', ''))
        weather = weather_map.get(scenario.get('weather', ''), scenario.get('weather', ''))
        obstacles = scenario.get('obstacles', [])
        obs_map = {'building': '建筑物', 'tree': '树木', 'lamp_post': '路灯', 'wind_turbine': '风力发电机', 'power_line': '电线', 'bird': '鸟类'}
        obs_names = [obs_map.get(o, o) for o in obstacles]

        desc = f"在{terrain}地形上，天气{weather}"
        if obs_names:
            desc += f"，存在{', '.join(obs_names)}等障碍物"
        return desc

    def generate_environment(self, config, batch_count=1):
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

    def export_environment(self, env_id, config, fmt='json'):
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

    def import_environment(self, import_file, fmt='json'):
        with open(import_file, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_config(content, fmt)
