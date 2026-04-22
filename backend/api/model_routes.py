from api import routes, get_current_user
from flask import request, jsonify, send_file
from models import db
from models.model import Model
from flask_jwt_extended import jwt_required
import os
import uuid
import json


@routes.route('/api/models', methods=['GET'])
@jwt_required()
def get_models():
    current_user = get_current_user()
    project_id = request.args.get('project_id')
    model_type = request.args.get('model_type')
    
    query = Model.query
    if project_id:
        query = query.filter_by(project_id=project_id)
    if model_type:
        query = query.filter_by(model_type=model_type)
    
    models = query.all()
    
    return jsonify([{
        'id': model.id,
        'model_name': model.model_name,
        'model_id': model.model_id,
        'project_id': model.project_id,
        'task_id': model.task_id,
        'model_type': model.model_type,
        'version': model.version,
        'description': model.description,
        'status': model.status,
        'created_at': model.created_at.isoformat()
    } for model in models])


@routes.route('/api/models', methods=['POST'])
@jwt_required()
def upload_model():
    current_user = get_current_user()
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    project_id = request.form.get('project_id')
    task_id = request.form.get('task_id')
    model_type = request.form.get('model_type')
    version = request.form.get('version', '1.0.0')
    description = request.form.get('description', '')
    
    # 生成模型ID
    serial_no = str(uuid.uuid4().hex[:4])
    model_id = f"SERI_MDL_{project_id}_{task_id}_{model_type}_{serial_no}"
    
    # 确保存储目录存在
    upload_dir = f"uploads/models/{project_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # 保存文件
    file_path = os.path.join(upload_dir, file.filename)
    file.save(file_path)
    
    # 创建模型记录
    new_model = Model(
        model_name=file.filename,
        model_id=model_id,
        project_id=project_id,
        task_id=task_id,
        model_type=model_type,
        version=version,
        description=description,
        file_path=file_path
    )
    
    db.session.add(new_model)
    db.session.commit()
    
    return jsonify({'message': 'Model uploaded successfully', 'model': {
        'id': new_model.id,
        'model_id': new_model.model_id,
        'model_name': new_model.model_name
    }}), 201


@routes.route('/api/models/<int:model_id>', methods=['GET'])
@jwt_required()
def download_model(model_id):
    current_user = get_current_user()
    model = Model.query.get(model_id)
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    if not os.path.exists(model.file_path):
        return jsonify({'error': 'Model file not found'}), 404
    
    return send_file(model.file_path, as_attachment=True)


@routes.route('/api/models/<int:model_id>', methods=['PUT'])
@jwt_required()
def update_model(model_id):
    current_user = get_current_user()
    model = Model.query.get(model_id)
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    data = request.get_json()
    model.model_name = data.get('model_name', model.model_name)
    model.description = data.get('description', model.description)
    model.status = data.get('status', model.status)
    
    db.session.commit()
    
    return jsonify({'message': 'Model updated successfully'})


@routes.route('/api/models/<int:model_id>', methods=['DELETE'])
@jwt_required()
def delete_model(model_id):
    current_user = get_current_user()
    model = Model.query.get(model_id)
    
    if not model:
        return jsonify({'error': 'Model not found'}), 404
    
    # 删除文件
    if os.path.exists(model.file_path):
        os.remove(model.file_path)
    
    db.session.delete(model)
    db.session.commit()
    
    return jsonify({'message': 'Model deleted successfully'})
