from api import routes, get_current_user
from flask import request, jsonify
from models import db
from models.user import User
from flask_jwt_extended import create_access_token, jwt_required
import json


@routes.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if not user or user.password != password:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    identity = json.dumps({'id': user.id, 'username': user.username, 'role': user.role})
    access_token = create_access_token(identity=identity)
    return jsonify({'access_token': access_token, 'user': {'id': user.id, 'username': user.username, 'role': user.role}})


@routes.route('/api/auth/register', methods=['POST'])
@jwt_required()
def register():
    current_user = get_current_user()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if User.query.filter_by(username=username).first():
        return jsonify({'error': 'User already exists'}), 400
    
    new_user = User(username=username, password=password, role=role)
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({'message': 'User created successfully'}), 201


@routes.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    current_user = get_current_user()
    if current_user['role'] != 'admin':
        return jsonify({'error': 'Admin only'}), 403
    
    users = User.query.all()
    return jsonify([{'id': user.id, 'username': user.username, 'role': user.role, 'created_at': user.created_at.isoformat() if user.created_at else None} for user in users])
