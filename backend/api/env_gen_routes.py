from api import routes, get_current_user
from flask import request, jsonify
from services.enhanced_env_generator import EnhancedEnvGenerator
from flask_jwt_extended import jwt_required
import os
import json
import uuid


@routes.route('/api/env/templates', methods=['GET'])
@jwt_required()
def get_templates():
    from models.env_template import EnvTemplate

    # 获取查询参数
    template_type = request.args.get('type')
    complexity = request.args.get('complexity')
    source = request.args.get('source', 'all')  # all, built_in, custom

    # 初始化增强版生成器
    env_gen = EnhancedEnvGenerator()

    # 获取内置模板
    built_in_templates = []
    if source in ['all', 'built_in']:
        built_in_filters = {}
        if template_type:
            built_in_filters['type'] = template_type
        if complexity:
            built_in_filters['complexity'] = complexity
        built_in_templates = env_gen.get_template_library(built_in_filters)

    # 获取自定义模板（数据库）
    custom_templates = []
    if source in ['all', 'custom']:
        query = EnvTemplate.query
        if template_type:
            query = query.filter_by(type=template_type)
        if complexity:
            query = query.filter_by(complexity=complexity)

        db_templates = query.all()
        custom_templates = [{
            'id': t.id,
            'template_id': t.template_id,
            'name': t.name,
            'type': t.type,
            'complexity': t.complexity,
            'test_type': t.test_type,
            'config': json.loads(t.config),
            'created_at': t.created_at.isoformat(),
            'source': 'custom'
        } for t in db_templates]

    # 合并结果，内置模板在前
    all_templates = [
        {**t, 'source': 'built_in'} for t in built_in_templates
    ] + custom_templates

    return jsonify(all_templates)


@routes.route('/api/env/templates/<template_id>', methods=['GET'])
@jwt_required()
def get_template(template_id):
    from models.env_template import EnvTemplate

    # 先尝试从内置模板库查找
    env_gen = EnhancedEnvGenerator()
    built_in_template = env_gen.get_template(template_id)

    if built_in_template:
        return jsonify({**built_in_template, 'source': 'built_in'})

    # 如果不在内置模板库，则从数据库查找
    template = EnvTemplate.query.filter_by(template_id=template_id).first()
    if not template:
        return jsonify({'error': 'Template not found'}), 404

    return jsonify({
        'id': template.id,
        'template_id': template.template_id,
        'name': template.name,
        'type': template.type,
        'complexity': template.complexity,
        'test_type': template.test_type,
        'config': json.loads(template.config),
        'created_at': template.created_at.isoformat(),
        'source': 'custom'
    })


@routes.route('/api/env/templates', methods=['POST'])
@jwt_required()
def create_template():
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    name = data.get('name')
    template_type = data.get('type', 'custom')
    complexity = data.get('complexity', 'medium')
    test_type = data.get('test_type', 'general')
    config = data.get('config')

    from models.env_template import EnvTemplate
    from models import db

    template_id = f"TPL_{uuid.uuid4().hex[:8]}"
    template = EnvTemplate(
        template_id=template_id,
        name=name,
        type=template_type,
        complexity=complexity,
        test_type=test_type,
        config=json.dumps(config),
        created_by=current_user['id']
    )
    db.session.add(template)
    db.session.commit()

    return jsonify({'message': 'Template created successfully', 'template_id': template_id}), 201


@routes.route('/api/env/templates/<template_id>', methods=['PUT'])
@jwt_required()
def update_template(template_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config']:
        return jsonify({'error': 'Permission denied'}), 403

    from models.env_template import EnvTemplate
    from models import db

    template = EnvTemplate.query.filter_by(template_id=template_id).first()
    if not template:
        return jsonify({'error': 'Template not found'}), 404

    data = request.get_json()
    template.name = data.get('name', template.name)
    template.type = data.get('type', template.type)
    template.complexity = data.get('complexity', template.complexity)
    template.test_type = data.get('test_type', template.test_type)
    if 'config' in data:
        template.config = json.dumps(data['config'])

    db.session.commit()

    return jsonify({'message': 'Template updated successfully'})


@routes.route('/api/env/templates/<template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config']:
        return jsonify({'error': 'Permission denied'}), 403

    from models.env_template import EnvTemplate
    from models import db

    template = EnvTemplate.query.filter_by(template_id=template_id).first()
    if not template:
        return jsonify({'error': 'Template not found'}), 404

    db.session.delete(template)
    db.session.commit()

    return jsonify({'message': 'Template deleted successfully'})


@routes.route('/api/env/generate', methods=['POST'])
@jwt_required()
def generate_environment():
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    config = data.get('config')
    batch_count = data.get('batch_count', 1)
    project_id = data.get('project_id')
    env_name = data.get('env_name', 'Generated Environment')
    desc_format = data.get('desc_format', 'json')
    template_id = data.get('template_id')  # 支持基于模板生成

    env_gen = EnhancedEnvGenerator()

    # 验证配置
    if config:
        if desc_format == 'xml' and isinstance(config, str):
            config = env_gen.parse_config(config, 'xml')

        # 验证配置有效性
        is_valid, errors = env_gen.validate_config(config)
        if not is_valid:
            return jsonify({'error': 'Invalid configuration', 'errors': errors}), 400

        environments = env_gen.generate_environment(config, batch_count)
    elif template_id:
        # 基于模板生成
        variations = data.get('variations', 1)
        try:
            environments = env_gen.generate_from_template(template_id, variations)
        except ValueError as e:
            return jsonify({'error': str(e)}), 400
    else:
        return jsonify({'error': 'Either config or template_id must be provided'}), 400

    from models import db
    from models.environment import Environment

    saved_envs = []
    for env in environments:
        new_env = Environment(
            env_name=env_name,
            env_id=env['env_id'],
            project_id=project_id,
            config=json.dumps(env['config']),
            desc_format=desc_format,
            preview_data=json.dumps(env['preview_data'])
        )
        db.session.add(new_env)
        saved_envs.append({
            'id': new_env.id,
            'env_id': new_env.env_id,
            'env_name': new_env.env_name,
            'preview_data': env['preview_data']
        })

    db.session.commit()

    return jsonify({'message': 'Environment(s) generated successfully', 'environments': saved_envs}), 201


@routes.route('/api/env/export/<env_id>', methods=['GET'])
@jwt_required()
def export_environment(env_id):
    current_user = get_current_user()

    from models.environment import Environment
    env = Environment.query.filter_by(env_id=env_id).first()
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    fmt = request.args.get('format', 'json')
    env_gen = EnhancedEnvGenerator()
    export_path = env_gen.export_environment(env_id, json.loads(env.config), fmt)

    from flask import send_file
    return send_file(export_path, as_attachment=True)


@routes.route('/api/env/import', methods=['POST'])
@jwt_required()
def import_environment():
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config']:
        return jsonify({'error': 'Permission denied'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    project_id = request.form.get('project_id')
    env_name = request.form.get('env_name', 'Imported Environment')

    filename = file.filename
    if filename.endswith('.xml'):
        fmt = 'xml'
    else:
        fmt = 'json'

    import_dir = 'imports/environments'
    os.makedirs(import_dir, exist_ok=True)
    file_path = os.path.join(import_dir, filename)
    file.save(file_path)

    env_gen = EnhancedEnvGenerator()
    config = env_gen.import_environment(file_path, fmt)

    # 验证导入的配置
    is_valid, errors = env_gen.validate_config(config)
    if not is_valid:
        return jsonify({'error': 'Invalid imported configuration', 'errors': errors}), 400

    from models import db
    from models.environment import Environment

    env_id = f"ENV_{uuid.uuid4().hex[:8]}"
    preview = env_gen.generate_preview(config)
    new_env = Environment(
        env_name=env_name,
        env_id=env_id,
        project_id=project_id,
        config=json.dumps(config),
        desc_format=fmt,
        preview_data=json.dumps(preview)
    )

    db.session.add(new_env)
    db.session.commit()

    return jsonify({'message': 'Environment imported successfully', 'environment': {
        'id': new_env.id,
        'env_id': new_env.env_id,
        'env_name': new_env.env_name,
        'preview_data': preview
    }}), 201


@routes.route('/api/env/parse-config', methods=['POST'])
@jwt_required()
def parse_config():
    current_user = get_current_user()
    data = request.get_json()
    config_content = data.get('config_content')
    config_format = data.get('config_format', 'json')

    env_gen = EnhancedEnvGenerator()
    try:
        config = env_gen.parse_config(config_content, config_format)
        preview = env_gen.generate_preview(config)
        return jsonify({'config': config, 'preview': preview})
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@routes.route('/api/env/config-to-xml', methods=['POST'])
@jwt_required()
def config_to_xml():
    current_user = get_current_user()
    data = request.get_json()
    config = data.get('config')

    env_gen = EnhancedEnvGenerator()
    xml_content = env_gen.config_to_xml(config)
    return jsonify({'xml': xml_content})


@routes.route('/api/env/metadata', methods=['GET'])
@jwt_required()
def get_env_metadata():
    """获取环境生成器的元数据（支持的类型、选项等）"""
    env_gen = EnhancedEnvGenerator()

    metadata = {
        'terrain_types': [
            {'value': k, 'name': v['name'], 'complexity': v['complexity']}
            for k, v in env_gen.terrain_types.items()
        ],
        'weather_types': [
            {'value': k, 'name': v['name'], 'complexity': v['complexity']}
            for k, v in env_gen.weather_types.items()
        ],
        'obstacle_types': [
            {'value': k, 'name': v['name'], 'complexity': v['complexity']}
            for k, v in env_gen.obstacle_types.items()
        ],
        'dynamics_types': [
            {'value': k, 'name': v['name'], 'complexity': v['complexity']}
            for k, v in env_gen.dynamics_types.items()
        ],
        'aero_types': [
            {'value': k, 'name': v['name'], 'complexity': v['complexity']}
            for k, v in env_gen.aero_types.items()
        ]
    }

    return jsonify(metadata)
