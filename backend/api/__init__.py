from flask import Blueprint
import json
from flask_jwt_extended import get_jwt_identity


routes = Blueprint('api', __name__)


def get_current_user():
    identity = get_jwt_identity()
    if isinstance(identity, str):
        return json.loads(identity)
    return identity


from .user_routes import *
from .project_routes import *
from .environment_routes import *
from .model_routes import *
from .adjustment_routes import *
from .env_gen_routes import *
from .env_adjust_routes import *
from .env_optimize_routes import *
from .model_mgr_routes import *
