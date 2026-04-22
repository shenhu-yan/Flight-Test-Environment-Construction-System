from api import routes, get_current_user
from flask import request, jsonify
from models import db
from models.environment import Environment
from flask_jwt_extended import jwt_required
import json
import uuid


@routes.route('/api/environments', methods=['GET'])
@jwt_required()
def get_environments():
    current_user = get_current_user()
    project_id = request.args.get('project_id')

    if project_id:
        environments = Environment.query.filter_by(project_id=project_id).all()
    else:
        environments = Environment.query.all()

    return jsonify([{
        'id': env.id,
        'env_name': env.env_name,
        'env_id': env.env_id,
        'project_id': env.project_id,
        'config': json.loads(env.config),
        'desc_format': env.desc_format,
        'status': env.status,
        'preview_data': json.loads(env.preview_data) if env.preview_data else None,
        'created_at': env.created_at.isoformat(),
        'updated_at': env.updated_at.isoformat()
    } for env in environments])


@routes.route('/api/environments', methods=['POST'])
@jwt_required()
def create_environment():
    current_user = get_current_user()

    data = request.get_json()
    env_name = data.get('env_name')
    project_id = data.get('project_id')
    config = data.get('config')
    batch_count = data.get('batch_count', 1)
    desc_format = data.get('desc_format', 'json')

    from services.env_generator import EnvGenerator
    env_gen = EnvGenerator()

    if desc_format == 'xml':
        config = env_gen.parse_config(config, 'xml')

    environments = []
    for i in range(batch_count):
        env_id = f"ENV_{uuid.uuid4().hex[:8]}"
        preview = env_gen.generate_preview(config)
        new_env = Environment(
            env_name=f"{env_name}_{i+1}" if batch_count > 1 else env_name,
            env_id=env_id,
            project_id=project_id,
            config=json.dumps(config),
            desc_format=desc_format,
            preview_data=json.dumps(preview)
        )
        db.session.add(new_env)
        environments.append(new_env)

    db.session.commit()

    return jsonify({'message': 'Environment(s) created successfully', 'environments': [{
        'id': env.id,
        'env_name': env.env_name,
        'env_id': env.env_id,
        'project_id': env.project_id,
        'preview_data': json.loads(env.preview_data) if env.preview_data else None
    } for env in environments]}), 201


@routes.route('/api/environments/<int:env_id>', methods=['GET'])
@jwt_required()
def get_environment(env_id):
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404
    return jsonify({
        'id': env.id,
        'env_name': env.env_name,
        'env_id': env.env_id,
        'project_id': env.project_id,
        'config': json.loads(env.config),
        'desc_format': env.desc_format,
        'status': env.status,
        'preview_data': json.loads(env.preview_data) if env.preview_data else None,
        'created_at': env.created_at.isoformat(),
        'updated_at': env.updated_at.isoformat()
    })


@routes.route('/api/environments/<int:env_id>', methods=['PUT'])
@jwt_required()
def update_environment(env_id):
    current_user = get_current_user()
    env = Environment.query.get(env_id)

    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    data = request.get_json()
    new_config = data.get('config', json.loads(env.config))
    env.env_name = data.get('env_name', env.env_name)
    env.config = json.dumps(new_config)
    env.status = data.get('status', env.status)

    from services.env_generator import EnvGenerator
    env_gen = EnvGenerator()
    preview = env_gen.generate_preview(new_config)
    env.preview_data = json.dumps(preview)

    db.session.commit()

    return jsonify({'message': 'Environment updated successfully'})


@routes.route('/api/environments/<int:env_id>', methods=['DELETE'])
@jwt_required()
def delete_environment(env_id):
    current_user = get_current_user()
    env = Environment.query.get(env_id)

    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    db.session.delete(env)
    db.session.commit()

    return jsonify({'message': 'Environment deleted successfully'})


@routes.route('/api/environments/<int:env_id>/preview', methods=['GET'])
@jwt_required()
def preview_environment(env_id):
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    if env.preview_data:
        return jsonify({
            'env_id': env.id,
            'env_name': env.env_name,
            'preview': json.loads(env.preview_data)
        })

    from services.env_generator import EnvGenerator
    env_gen = EnvGenerator()
    config = json.loads(env.config)
    preview = env_gen.generate_preview(config)
    env.preview_data = json.dumps(preview)
    db.session.commit()

    return jsonify({
        'env_id': env.id,
        'env_name': env.env_name,
        'preview': preview
    })


@routes.route('/api/environments/<int:env_id>/preview', methods=['POST'])
@jwt_required()
def preview_environment_config(env_id):
    current_user = get_current_user()
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    data = request.get_json()
    config = data.get('config', json.loads(env.config))

    from services.env_generator import EnvGenerator
    env_gen = EnvGenerator()
    preview = env_gen.generate_preview(config)

    return jsonify({
        'env_id': env.id,
        'env_name': env.env_name,
        'preview': preview
    })


@routes.route('/api/environments/preview-config', methods=['POST'])
@jwt_required()
def preview_config():
    current_user = get_current_user()
    data = request.get_json()
    config = data.get('config')
    desc_format = data.get('desc_format', 'json')

    from services.env_generator import EnvGenerator
    env_gen = EnvGenerator()

    if desc_format == 'xml' and isinstance(config, str):
        config = env_gen.parse_config(config, 'xml')

    preview = env_gen.generate_preview(config)

    return jsonify({'preview': preview})


@routes.route('/api/environments/<int:env_id>/adjust', methods=['POST'])
@jwt_required()
def adjust_environment(env_id):
    current_user = get_current_user()
    env = Environment.query.get(env_id)

    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    data = request.get_json()
    new_config = data.get('config')
    trigger = data.get('trigger', 'manual')
    reason = data.get('reason')

    env.config = json.dumps(new_config)
    env.status = 'adjusted'

    from services.env_generator import EnvGenerator
    env_gen = EnvGenerator()
    preview = env_gen.generate_preview(new_config)
    env.preview_data = json.dumps(preview)

    from models.adjustment import Adjustment
    adjustment = Adjustment(
        env_id=env.id,
        adjuster=current_user['username'],
        trigger=trigger,
        params=json.dumps(new_config),
        reason=reason
    )
    db.session.add(adjustment)
    db.session.commit()

    return jsonify({'message': 'Environment adjusted successfully'})
