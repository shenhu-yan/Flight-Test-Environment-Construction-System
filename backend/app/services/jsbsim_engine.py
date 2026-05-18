import logging
from typing import Any

from app.schemas.env_config import EnvConfig

logger = logging.getLogger(__name__)


class JSBSimEngine:
    def __init__(self):
        self._sim = None
        try:
            import jsbsim
            self._sim = jsbsim.FGFDMExec(None)
            logger.info("JSBSim engine initialized successfully")
        except ImportError:
            logger.warning("JSBSim not available, using mock engine")

    def build_environment(self, config: EnvConfig) -> dict[str, Any]:
        groundXML = self._build_ground_xml(config)
        weatherXML = self._build_weather_xml(config)
        aircraftXML = self._build_aircraft_xml(config)
        flightXML = self._build_flight_xml(config)

        return {
            "ground_xml": groundXML,
            "weather_xml": weatherXML,
            "aircraft_xml": aircraftXML,
            "flight_xml": flightXML,
            "jsbsim_config": {
                "aircraft_model": config.flight_dynamics.aircraft_model,
                "mass": config.flight_dynamics.mass,
                "wingspan": config.flight_dynamics.wingspan,
                "wind_speed": config.weather.wind_speed,
                "wind_direction": config.weather.wind_direction,
                "visibility": config.weather.visibility,
                "terrain_type": config.terrain.type,
                "elevation_min": config.terrain.elevation_min,
                "elevation_max": config.terrain.elevation_max,
            },
        }

    def _build_ground_xml(self, config: EnvConfig) -> str:
        terrain = config.terrain
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<ground xmlns:xi="http://www.w3.org/2001/XInclude">',
            f'  <terrain type="{terrain.type}">',
            f'    <elevation-min>{terrain.elevation_min}</elevation-min>',
            f'    <elevation-max>{terrain.elevation_max}</elevation-max>',
            f'    <resolution>{terrain.resolution}</resolution>',
            "  </terrain>",
        ]
        for wp in config.waypoints:
            xml_parts.append(
                f'  <waypoint id="{wp.id}" x="{wp.position[0]}" '
                f'y="{wp.position[1]}" z="{wp.position[2]}" />'
            )
        for i, obstacle in enumerate(config.obstacles.types):
            xml_parts.append(f'  <obstacle id="obs_{i}" type="{obstacle}" />')
        xml_parts.append("</ground>")
        return "\n".join(xml_parts)

    def _build_weather_xml(self, config: EnvConfig) -> str:
        w = config.weather
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<weather>
  <wind>
    <wind-speed-unit>KT</wind-speed-unit>
    <wind-speed>{w.wind_speed}</wind-speed>
    <wind-direction-deg>{w.wind_direction}</wind-direction-deg>
  </wind>
  <visibility>
    <visibility-unit>FT</visibility-unit>
    <visibility>{w.visibility}</visibility>
  </visibility>
</weather>"""

    def _build_aircraft_xml(self, config: EnvConfig) -> str:
        fd = config.flight_dynamics
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<aircraft name="{fd.aircraft_model}">
  <mass>{fd.mass}</mass>
  <wingspan>{fd.wingspan}</wingspan>
</aircraft>"""

    def _build_flight_xml(self, config: EnvConfig) -> str:
        xml_parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<flight-plan>',
            "  <waypoints>",
        ]
        for wp in config.waypoints:
            xml_parts.append(
                f'    <waypoint id="{wp.id}" x="{wp.position[0]}" '
                f'y="{wp.position[1]}" z="{wp.position[2]}" order="{wp.order}" />'
            )
        xml_parts.append("  </waypoints>")
        xml_parts.append("</flight-plan>")
        return "\n".join(xml_parts)

    def run_simulation_step(self, config: EnvConfig) -> dict[str, Any]:
        if self._sim is not None:
            try:
                self._sim.run()
                return {
                    "altitude": self._sim["position/h-sl-ft"],
                    "latitude": self._sim["position/lat-geod-deg"],
                    "longitude": self._sim["position/long-geod-deg"],
                    "velocity": self._sim["velocities/v-north-fps"],
                    "success": True,
                }
            except Exception as e:
                logger.error(f"JSBSim simulation error: {e}")
                return {"error": str(e), "success": False}
        return {
            "altitude": 1000.0,
            "latitude": 0.0,
            "longitude": 0.0,
            "velocity": 0.0,
            "success": True,
            "mock": True,
        }


jsbsim_engine = JSBSimEngine()
