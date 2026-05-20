from app.schemas.env_config import EnvConfig


class JSBSimEngine:
    def __init__(self, config: EnvConfig):
        self.config = config
        self.fdm = None

    def build_environment(self) -> dict:
        aircraft_xml = self._generate_aircraft_xml()
        atmosphere_xml = self._generate_atmosphere_xml()
        terrain_xml = self._generate_terrain_xml()

        return {
            "aircraft_xml": aircraft_xml,
            "atmosphere_xml": atmosphere_xml,
            "terrain_xml": terrain_xml,
        }

    def _generate_aircraft_xml(self) -> str:
        aircraft = self.config.aircraft
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<fdm_config name="{aircraft.model}" version="2.0">
  <ground_reactions>
    <gear_unit name="NOSEGEAR" type="BOGEY">
      <location name="unitx" unit="IN">
        <x>0</x>
        <y>0</y>
        <z>0</z>
      </location>
      <static_friction>0.8</static_friction>
      <dynamic_friction>0.5</dynamic_friction>
    </gear_unit>
  </ground_reactions>
  <mass balance_type="POINT_MASS">
    <ixx>12875.0</ixx>
    <iyy>18249.0</iyy>
    <izz>26667.0</izz>
    <ixz>2275.0</ixz>
    <emptywt>{aircraft.mass * 9.81}</emptywt>
  </mass>
</fdm_config>"""

    def _generate_atmosphere_xml(self) -> str:
        atm = self.config.atmosphere
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<atmosphere>
  <wind>
    <north>{atm.wind_speed * __import__('math').cos(__import__('math').radians(atm.wind_direction))}</north>
    <east>{atm.wind_speed * __import__('math').sin(__import__('math').radians(atm.wind_direction))}</east>
    <down>0</down>
  </wind>
  <visibility>{atm.visibility}</visibility>
</atmosphere>"""

    def _generate_terrain_xml(self) -> str:
        terrain = self.config.terrain
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<terrain>
  <type>{terrain.type.value}</type>
  <elevation_min>{terrain.elevation_min}</elevation_min>
  <elevation_max>{terrain.elevation_max}</elevation_max>
  <resolution>{terrain.resolution}</resolution>
</terrain>"""

    def reset(self):
        if self.fdm:
            self.fdm.reset_to_initial_conditions(0)

    def step(self, action: dict) -> dict:
        return {
            "position": [0, 0, 100],
            "velocity": [0, 0, 0],
            "attitude": [0, 0, 0],
        }
