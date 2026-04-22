from api import routes, get_current_user
from flask import request, jsonify
from models import db
from models.project import Project
from flask_jwt_extended import jwt_required


@routes.route('/api/projects', methods=['GET'])
@jwt_required()
def get_projects():
    current_user = get_current_user()
    
    if current_user['role'] == 'admin':
        projects = Project.query.all()
    else:
        projects = Project.query.filter_by(created_by=current_user['id']).all()
    
    return jsonify([{
        'id': project.id,
        'project_name': project.project_name,
        'project_id': project.project_id,
        'description': project.description,
        'created_by': project.created_by,
        'created_at': project.created_at.isoformat()
    } for project in projects])


@routes.route('/api/projects', methods=['POST'])
@jwt_required()
def create_project():
    current_user = get_current_user()
    
    data = request.get_json()
    project_name = data.get('project_name')
    project_id = data.get('project_id')
    description = data.get('description')
    
    if Project.query.filter_by(project_id=project_id).first():
        return jsonify({'error': 'Project ID already exists'}), 400
    
    new_project = Project(
        project_name=project_name,
        project_id=project_id,
        description=description,
        created_by=current_user['id']
    )
    
    db.session.add(new_project)
    db.session.commit()
    
    return jsonify({'message': 'Project created successfully', 'project': {
        'id': new_project.id,
        'project_name': new_project.project_name,
        'project_id': new_project.project_id,
        'description': new_project.description
    }}), 201


@routes.route('/api/projects/<int:project_id>', methods=['PUT'])
@jwt_required()
def update_project(project_id):
    current_user = get_current_user()
    project = Project.query.get(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if current_user['role'] != 'admin' and project.created_by != current_user['id']:
        return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    project.project_name = data.get('project_name', project.project_name)
    project.description = data.get('description', project.description)
    
    db.session.commit()
    
    return jsonify({'message': 'Project updated successfully'})


@routes.route('/api/projects/<int:project_id>', methods=['DELETE'])
@jwt_required()
def delete_project(project_id):
    current_user = get_current_user()
    project = Project.query.get(project_id)
    
    if not project:
        return jsonify({'error': 'Project not found'}), 404
    
    if current_user['role'] != 'admin' and project.created_by != current_user['id']:
        return jsonify({'error': 'Permission denied'}), 403
    
    db.session.delete(project)
    db.session.commit()
    
    return jsonify({'message': 'Project deleted successfully'})
