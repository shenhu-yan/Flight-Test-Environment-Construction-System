from api import routes, get_current_user
from flask import request, jsonify, send_file
from services.model_manager import ModelManager
from flask_jwt_extended import jwt_required
import os
import json


@routes.route('/api/models/mgr/upload', methods=['POST'])
@jwt_required()
def upload_model_mgr():
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    project_id = request.form.get('project_id')
    task_id = request.form.get('task_id')
    model_type = request.form.get('model_type')
    version = request.form.get('version', '1.0.0')
    description = request.form.get('description', '')
    
    model_manager = ModelManager()
    upload_result = model_manager.upload_model(
        file=file,
        project_id=project_id,
        task_id=task_id,
        model_type=model_type,
        version=version,
        description=description
    )
    
    from models import db
    from models.model import Model
    
    new_model = Model(
        model_name=upload_result['file_name'],
        model_id=upload_result['model_id'],
        project_id=project_id,
        task_id=task_id,
        model_type=model_type,
        version=version,
        description=description,
        file_path=upload_result['file_path']
    )
    
    db.session.add(new_model)
    db.session.commit()
    
    return jsonify({'message': 'Model uploaded successfully', 'model': {
        'id': new_model.id,
        'model_id': new_model.model_id,
        'model_name': new_model.model_name,
        'project_id': new_model.project_id,
        'task_id': new_model.task_id,
        'model_type': new_model.model_type,
        'version': new_model.version
    }}), 201


@routes.route('/api/models/mgr/download/<model_id>', methods=['GET'])
@jwt_required()
def download_model_mgr(model_id):
    current_user = get_current_user()
    
    from models.model import Model
    model = Model.query.filter_by(model_id=model_id).first()
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    if current_user['role'] != 'admin':
        from models.project import Project
        project = Project.query.get(model.project_id)
        if not project or project.created_by != current_user['id']:
            return jsonify({'error': 'Permission denied'}), 403
    
    model_manager = ModelManager()
    file_path = model_manager.download_model(model_id, str(model.project_id))
    
    if not file_path:
        return jsonify({'error': 'Model file not found'}), 404
    
    return send_file(file_path, as_attachment=True)


@routes.route('/api/models/mgr/delete/<int:model_id>', methods=['DELETE'])
@jwt_required()
def delete_model_mgr(model_id):
    current_user = get_current_user()
    
    from models.model import Model
    model = Model.query.get(model_id)
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    if current_user['role'] != 'admin':
        from models.project import Project
        project = Project.query.get(model.project_id)
        if not project or project.created_by != current_user['id']:
            return jsonify({'error': 'Permission denied'}), 403
    
    model_manager = ModelManager()
    model_manager.delete_model(model.model_id, str(model.project_id))
    
    from models import db
    db.session.delete(model)
    db.session.commit()
    
    return jsonify({'message': 'Model deleted successfully'})


@routes.route('/api/models/mgr/list', methods=['GET'])
@jwt_required()
def list_models():
    current_user = get_current_user()
    project_id = request.args.get('project_id')
    model_type = request.args.get('model_type')
    
    if current_user['role'] != 'admin' and project_id:
        from models.project import Project
        project = Project.query.get(project_id)
        if not project or project.created_by != current_user['id']:
            return jsonify({'error': 'Permission denied'}), 403
    
    model_manager = ModelManager()
    models = model_manager.list_models(project_id, model_type)
    
    return jsonify(models)


@routes.route('/api/models/mgr/info/<model_id>', methods=['GET'])
@jwt_required()
def get_model_info(model_id):
    current_user = get_current_user()
    
    from models.model import Model
    model = Model.query.filter_by(model_id=model_id).first()
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    if current_user['role'] != 'admin':
        from models.project import Project
        project = Project.query.get(model.project_id)
        if not project or project.created_by != current_user['id']:
            return jsonify({'error': 'Permission denied'}), 403
    
    model_manager = ModelManager()
    model_info = model_manager.get_model_info(model_id, str(model.project_id))
    
    if not model_info:
        return jsonify({'error': 'Model file not found'}), 404
    
    return jsonify(model_info)


@routes.route('/api/models/mgr/versions', methods=['GET'])
@jwt_required()
def get_model_versions():
    current_user = get_current_user()
    project_id = request.args.get('project_id')
    task_id = request.args.get('task_id')
    model_type = request.args.get('model_type')
    
    if current_user['role'] != 'admin':
        from models.project import Project
        project = Project.query.get(project_id)
        if not project or project.created_by != current_user['id']:
            return jsonify({'error': 'Permission denied'}), 403
    
    model_manager = ModelManager()
    versions = model_manager.get_model_versions(project_id, task_id, model_type)
    
    return jsonify(versions)


@routes.route('/api/models/mgr/backup/<project_id>', methods=['POST'])
@jwt_required()
def backup_project_models(project_id):
    current_user = get_current_user()
    
    if current_user['role'] != 'admin':
        from models.project import Project
        project = Project.query.get(project_id)
        if not project or project.created_by != current_user['id']:
            return jsonify({'error': 'Permission denied'}), 403
    
    model_manager = ModelManager()
    backup_path = model_manager.backup_project_models(project_id)
    
    if not backup_path:
        return jsonify({'error': 'Backup failed'}), 500
    
    return jsonify({'message': 'Models backed up successfully', 'backup_path': backup_path})


@routes.route('/api/models/mgr/restore/<project_id>', methods=['POST'])
@jwt_required()
def restore_project_models(project_id):
    current_user = get_current_user()
    
    if current_user['role'] != 'admin':
        from models.project import Project
        project = Project.query.get(project_id)
        if not project or project.created_by != current_user['id']:
            return jsonify({'error': 'Permission denied'}), 403
    
    data = request.get_json()
    backup_path = data.get('backup_path')
    
    if not backup_path or not os.path.exists(backup_path):
        return jsonify({'error': 'Invalid backup path'}), 400
    
    model_manager = ModelManager()
    success = model_manager.restore_project_models(project_id, backup_path)
    
    if success:
        return jsonify({'message': 'Models restored successfully'})
    else:
        return jsonify({'error': 'Restore failed'}), 500


@routes.route('/api/models/mgr/validate', methods=['POST'])
@jwt_required()
def validate_model():
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    temp_dir = 'temp'
    os.makedirs(temp_dir, exist_ok=True)
    temp_path = os.path.join(temp_dir, file.filename)
    file.save(temp_path)
    
    model_manager = ModelManager()
    valid, message = model_manager.validate_model(temp_path)
    
    os.remove(temp_path)
    
    return jsonify({'valid': valid, 'message': message})
