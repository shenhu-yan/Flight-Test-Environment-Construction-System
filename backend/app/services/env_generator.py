import json
import os
import tempfile
import zipfile
from io import BytesIO
from minio import Minio
from app.schemas.env_config import EnvConfig
from app.services.jsbsim_engine import JSBSimEngine
from app.core.config import settings


CORE_PY_TEMPLATE = '''
import gymnasium as gym
import numpy as np
import json
import os


class FlightEnv(gym.Env):
    metadata = {{"render_modes": ["human", "rgb_array"]}}

    def __init__(self, config_path: str, render_mode: str = None):
        super().__init__()
        self.render_mode = render_mode

        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.action_space = gym.spaces.Box(
            low=np.array([-1, -1, -1]),
            high=np.array([1, 1, 1]),
            dtype=np.float32
        )

        self.observation_space = gym.spaces.Box(
            low=np.array([-1000, -1000, -100, -180, -180, -180]),
            high=np.array([1000, 1000, 1000, 180, 180, 180]),
            dtype=np.float32
        )

        self.state = None
        self.step_count = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.state = np.array([0.0, 0.0, 100.0, 0.0, 0.0, 0.0], dtype=np.float32)
        self.step_count = 0
        return self.state, {{}}

    def step(self, action):
        self.step_count += 1

        self.state[0] += action[0] * 10
        self.state[1] += action[1] * 10
        self.state[2] += action[2] * 5

        reward = self._calculate_reward()
        terminated = self.state[2] <= 0 or self.state[2] > 1000
        truncated = self.step_count >= 1000

        return self.state, reward, terminated, truncated, {{}}

    def _calculate_reward(self):
        reward_items = self.config.get("reward", {{}}).get("items", [])
        reward = 0.0
        for item in reward_items:
            if item["name"] == "altitude_reward":
                reward += item["coefficient"] * self.state[2] / 100
        return reward

    def close(self):
        pass
'''

REWARD_PY_TEMPLATE = '''
def calculate_reward(state, action, config):
    reward = 0.0
    reward_items = config.get("reward", {}).get("items", [])
    for item in reward_items:
        if item["name"] == "altitude_reward":
            reward += item["coefficient"] * state[2] / 100
    return reward
'''


def generate_environment(env_id: str, config: EnvConfig, project_id: str, creator_id: str) -> dict:
    engine = JSBSimEngine(config)
    jsbsim_files = engine.build_environment()

    env_dir = tempfile.mkdtemp()

    os.makedirs(os.path.join(env_dir, "env", "jsbsim_config"), exist_ok=True)
    os.makedirs(os.path.join(env_dir, "preview"), exist_ok=True)

    with open(os.path.join(env_dir, "env", "__init__.py"), "w") as f:
        f.write("from .core import FlightEnv\n")

    with open(os.path.join(env_dir, "env", "core.py"), "w") as f:
        f.write(CORE_PY_TEMPLATE)

    with open(os.path.join(env_dir, "env", "reward.py"), "w") as f:
        f.write(REWARD_PY_TEMPLATE)

    with open(os.path.join(env_dir, "env", "jsbsim_config", "aircraft.xml"), "w") as f:
        f.write(jsbsim_files["aircraft_xml"])

    with open(os.path.join(env_dir, "env", "jsbsim_config", "atmosphere.xml"), "w") as f:
        f.write(jsbsim_files["atmosphere_xml"])

    with open(os.path.join(env_dir, "env", "jsbsim_config", "terrain.xml"), "w") as f:
        f.write(jsbsim_files["terrain_xml"])

    with open(os.path.join(env_dir, "config.json"), "w") as f:
        json.dump(config.model_dump(), f, indent=2)

    scene_data = generate_scene_data(config)
    with open(os.path.join(env_dir, "preview", "scene.json"), "w") as f:
        json.dump(scene_data, f, indent=2)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(env_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, env_dir)
                zipf.write(file_path, arcname)
    zip_buffer.seek(0)

    minio_client = Minio(
        settings.MINIO_ENDPOINT,
        access_key=settings.MINIO_ACCESS_KEY,
        secret_key=settings.MINIO_SECRET_KEY,
        secure=False,
    )

    bucket_name = settings.MINIO_BUCKET
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

    storage_path = f"envs/{project_id}/{env_id}.zip"
    minio_client.put_object(
        bucket_name,
        storage_path,
        zip_buffer,
        length=zip_buffer.getbuffer().nbytes,
        content_type="application/zip",
    )

    import shutil
    shutil.rmtree(env_dir)

    return {
        "storage_path": storage_path,
        "config": config.model_dump(),
    }


def generate_scene_data(config: EnvConfig) -> dict:
    import numpy as np

    terrain = config.terrain
    grid_size = [100, 100]
    elevation = np.random.uniform(
        terrain.elevation_min,
        terrain.elevation_max,
        (grid_size[1], grid_size[0])
    ).tolist()

    obstacles = []
    for i in range(config.obstacles.count):
        obstacles.append({
            "type": config.obstacles.types[i % len(config.obstacles.types)] if config.obstacles.types else "building",
            "position": [np.random.uniform(0, 500), np.random.uniform(0, 500), 0],
            "size": [10, 10, 20],
        })

    waypoints = []
    for wp in config.waypoints:
        waypoints.append({
            "id": wp.id,
            "position": wp.position,
            "order": wp.order,
        })

    return {
        "terrain": {
            "grid_size": grid_size,
            "resolution": terrain.resolution,
            "elevation": elevation,
        },
        "obstacles": obstacles,
        "waypoints": waypoints,
        "wind": {
            "direction": [1.0, 0.5, 0.0],
            "speed": config.atmosphere.wind_speed,
            "variability": 0.3,
        },
        "runway": {
            "position": [0, 0, 0],
            "heading": 90,
            "length": 3000,
            "width": 60,
        },
    }
