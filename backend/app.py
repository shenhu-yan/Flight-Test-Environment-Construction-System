from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI', 'sqlite:///flight_test_env.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False') == 'True'
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-dev-secret-key')

CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

JWTManager(app)

from models import db
from models.user import User
from models.project import Project
from models.environment import Environment
from models.model import Model
from models.adjustment import Adjustment
from models.env_template import EnvTemplate
from models.optimization_record import OptimizationRecord
from models.optimization_schedule import OptimizationSchedule

db.init_app(app)

from api import routes
app.register_blueprint(routes)


@app.route('/')
def index():
    return jsonify({
        'name': 'Flight Test Environment Construction System',
        'version': '1.0.0',
        'status': 'running'
    })


@app.route('/api/health')
def health_check():
    return jsonify({'status': 'healthy'})


def create_default_users():
    default_users = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin'},
        {'username': 'config', 'password': 'config123', 'role': 'config'},
        {'username': 'dev', 'password': 'dev123', 'role': 'dev'},
        {'username': 'user', 'password': 'user123', 'role': 'viewer'}
    ]

    for user_data in default_users:
        user = User.query.filter_by(username=user_data['username']).first()
        if not user:
            new_user = User(**user_data)
            db.session.add(new_user)

    db.session.commit()


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        create_default_users()
    app.run(debug=True, host='0.0.0.0', port=5000)
