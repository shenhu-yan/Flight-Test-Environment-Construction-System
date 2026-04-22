from api import routes, get_current_user
from flask import request, jsonify
from services.enhanced_env_adjuster import EnhancedEnvAdjuster
from flask_jwt_extended import jwt_required
import json


@routes.route('/api/env/<int:env_id>/monitor', methods=['POST'])
@jwt_required()
def monitor_environment(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    performance_data = data.get('performance_data')

    env_adjuster = EnhancedEnvAdjuster()
    adjustment_needed, adjustment_reason, analysis = env_adjuster.monitor_performance(env_id, performance_data)

    # 获取环境信息
    from models.environment import Environment
    env = Environment.query.get(env_id)

    return jsonify({
        'adjustment_needed': adjustment_needed,
        'adjustment_reason': adjustment_reason,
        'reason_text': env_adjuster.adjustment_reasons.get(adjustment_reason, adjustment_reason),
        'analysis': analysis,
        'environment': {
            'env_id': env.env_id if env else None,
            'env_name': env.env_name if env else None
        }
    })


@routes.route('/api/env/<int:env_id>/auto-adjust', methods=['POST'])
@jwt_required()
def auto_adjust_environment(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    performance_data = data.get('performance_data')

    # 获取环境配置
    from models.environment import Environment
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    env_config = json.loads(env.config)

    # 监测性能
    env_adjuster = EnhancedEnvAdjuster()
    adjustment_needed, adjustment_reason, analysis = env_adjuster.monitor_performance(env_id, performance_data)

    if adjustment_needed:
        # 自动调整
        new_config = env_adjuster.auto_adjust(env_config, adjustment_reason, performance_data)

        # 更新环境配置
        env.config = json.dumps(new_config)
        env.status = 'adjusted'

        # 记录调整历史
        adjustment_id = env_adjuster.record_adjustment(
            env_id=env_id,
            adjuster=current_user['username'],
            trigger='auto',
            params=new_config,
            reason=adjustment_reason,
            performance_before=performance_data
        )

        from models import db
        db.session.commit()

        return jsonify({
            'message': 'Environment auto-adjusted successfully',
            'new_config': new_config,
            'adjustment_id': adjustment_id,
            'adjustment_reason': adjustment_reason,
            'reason_text': env_adjuster.adjustment_reasons.get(adjustment_reason, adjustment_reason),
            'analysis': analysis
        })
    else:
        return jsonify({
            'message': 'No adjustment needed',
            'analysis': analysis
        })


@routes.route('/api/env/<int:env_id>/manual-adjust', methods=['POST'])
@jwt_required()
def manual_adjust_environment(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    adjustment_params = data.get('adjustment_params')
    reason = data.get('reason', 'Manual adjustment')

    # 获取环境配置
    from models.environment import Environment
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    env_config = json.loads(env.config)

    # 手动调整
    env_adjuster = EnhancedEnvAdjuster()
    new_config = env_adjuster.manual_adjust(env_config, adjustment_params)

    # 更新环境配置
    env.config = json.dumps(new_config)
    env.status = 'adjusted'

    # 记录调整历史
    adjustment_id = env_adjuster.record_adjustment(
        env_id=env_id,
        adjuster=current_user['username'],
        trigger='manual',
        params=new_config,
        reason=reason
    )

    from models import db
    db.session.commit()

    return jsonify({
        'message': 'Environment manually adjusted successfully',
        'new_config': new_config,
        'adjustment_id': adjustment_id,
        'reason': reason
    })


@routes.route('/api/env/<int:env_id>/adjustments', methods=['GET'])
@jwt_required()
def get_env_adjustments(env_id):
    current_user = get_current_user()

    env_adjuster = EnhancedEnvAdjuster()
    adjustments = env_adjuster.get_adjustment_history(env_id)

    return jsonify(adjustments)


@routes.route('/api/env/<int:env_id>/rollback/<int:adjustment_id>', methods=['POST'])
@jwt_required()
def rollback_adjustment(env_id, adjustment_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    # 回滚调整
    env_adjuster = EnhancedEnvAdjuster()
    env = env_adjuster.rollback_adjustment(env_id, adjustment_id)

    if env:
        return jsonify({
            'message': 'Environment rolled back successfully',
            'current_config': json.loads(env.config)
        })
    else:
        return jsonify({'error': 'Rollback failed'}), 400


@routes.route('/api/env/<int:env_id>/batch-adjust', methods=['POST'])
@jwt_required()
def batch_adjust_environment(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    adjustment_params = data.get('adjustment_params')
    reason = data.get('reason', 'Batch adjustment')

    # 获取环境配置
    from models.environment import Environment
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    env_config = json.loads(env.config)

    # 批量调整
    env_adjuster = EnhancedEnvAdjuster()
    new_config = env_adjuster.manual_adjust(env_config, adjustment_params)

    # 更新环境配置
    env.config = json.dumps(new_config)
    env.status = 'adjusted'

    # 记录调整历史
    adjustment_id = env_adjuster.record_adjustment(
        env_id=env_id,
        adjuster=current_user['username'],
        trigger='batch',
        params=new_config,
        reason=reason
    )

    from models import db
    db.session.commit()

    return jsonify({
        'message': 'Environment batch adjusted successfully',
        'new_config': new_config,
        'adjustment_id': adjustment_id,
        'reason': reason
    })


@routes.route('/api/env/<int:env_id>/performance-trend', methods=['GET'])
@jwt_required()
def get_performance_trend(env_id):
    """获取环境性能趋势分析"""
    current_user = get_current_user()
    days = request.args.get('days', 7, type=int)

    env_adjuster = EnhancedEnvAdjuster()
    trend = env_adjuster.get_performance_trend(env_id, days)

    return jsonify(trend)
