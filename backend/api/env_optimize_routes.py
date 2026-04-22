from api import routes, get_current_user
from flask import request, jsonify
from services.env_optimizer import EnvOptimizer
from flask_jwt_extended import jwt_required
import json


@routes.route('/api/env/<int:env_id>/evaluate', methods=['POST'])
@jwt_required()
def evaluate_environment(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    performance_data = data.get('performance_data')

    from models.environment import Environment
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    env_config = json.loads(env.config)

    env_optimizer = EnvOptimizer()
    evaluation_results = env_optimizer.evaluate_environment(env_config, performance_data)

    return jsonify(evaluation_results)


@routes.route('/api/env/<int:env_id>/optimize', methods=['POST'])
@jwt_required()
def optimize_environment(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    performance_data = data.get('performance_data')
    custom_goals = data.get('custom_goals')

    from models.environment import Environment
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    original_config = json.loads(env.config)

    env_optimizer = EnvOptimizer()
    evaluation_results = env_optimizer.evaluate_environment(original_config, performance_data)
    optimized_config = env_optimizer.optimize_environment(original_config, evaluation_results, custom_goals)
    optimization_verification = env_optimizer.verify_optimization(original_config, optimized_config, performance_data)

    env.config = json.dumps(optimized_config)
    env.status = 'optimized'

    from services.env_generator import EnvGenerator
    env_gen = EnvGenerator()
    preview = env_gen.generate_preview(optimized_config)
    env.preview_data = json.dumps(preview)

    env_optimizer.record_optimization(
        env_id=env_id,
        optimizer=current_user['username'],
        trigger='manual',
        original_config=original_config,
        optimized_config=optimized_config,
        scores_before=evaluation_results.get('scores', {}),
        scores_after=optimization_verification.get('optimized_scores', {}),
        improvement=optimization_verification.get('improvement', 0),
        custom_goals=custom_goals
    )

    from models import db
    db.session.commit()

    return jsonify({
        'message': 'Environment optimized successfully',
        'original_config': original_config,
        'optimized_config': optimized_config,
        'evaluation_results': evaluation_results,
        'optimization_verification': optimization_verification
    })


@routes.route('/api/env/<int:env_id>/verify-optimization', methods=['POST'])
@jwt_required()
def verify_optimization(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    original_config = data.get('original_config')
    optimized_config = data.get('optimized_config')
    performance_data = data.get('performance_data')

    env_optimizer = EnvOptimizer()
    verification_results = env_optimizer.verify_optimization(original_config, optimized_config, performance_data)

    return jsonify(verification_results)


@routes.route('/api/env/<int:env_id>/schedule-optimization', methods=['POST'])
@jwt_required()
def schedule_optimization(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    interval = data.get('interval', 'daily')
    custom_goals = data.get('custom_goals')

    env_optimizer = EnvOptimizer()
    schedule_info = env_optimizer.schedule_optimization(
        env_id=env_id,
        interval=interval,
        user_id=current_user['id'],
        custom_goals=custom_goals
    )

    return jsonify(schedule_info)


@routes.route('/api/env/<int:env_id>/schedule-optimization', methods=['GET'])
@jwt_required()
def get_schedule_optimization(env_id):
    current_user = get_current_user()

    from models.optimization_schedule import OptimizationSchedule
    schedule = OptimizationSchedule.query.filter_by(env_id=env_id).first()
    if not schedule:
        return jsonify({'scheduled': False})

    return jsonify({
        'scheduled': True,
        'id': schedule.id,
        'interval': schedule.interval,
        'enabled': schedule.enabled,
        'last_run': schedule.last_run.isoformat() if schedule.last_run else None,
        'next_run': schedule.next_run.isoformat() if schedule.next_run else None,
        'custom_goals': json.loads(schedule.custom_goals) if schedule.custom_goals else None
    })


@routes.route('/api/env/<int:env_id>/schedule-optimization/toggle', methods=['POST'])
@jwt_required()
def toggle_schedule_optimization(env_id):
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    enabled = data.get('enabled', True)

    from models.optimization_schedule import OptimizationSchedule
    schedule = OptimizationSchedule.query.filter_by(env_id=env_id).first()
    if not schedule:
        return jsonify({'error': 'Schedule not found'}), 404

    env_optimizer = EnvOptimizer()
    result = env_optimizer.toggle_schedule(schedule.id, enabled)

    return jsonify(result)


@routes.route('/api/env/scheduled-optimizations', methods=['GET'])
@jwt_required()
def get_all_scheduled_optimizations():
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config']:
        return jsonify({'error': 'Permission denied'}), 403

    env_optimizer = EnvOptimizer()
    schedules = env_optimizer.get_scheduled_optimizations()

    return jsonify(schedules)


@routes.route('/api/env/<int:env_id>/optimization-history', methods=['GET'])
@jwt_required()
def get_optimization_history(env_id):
    current_user = get_current_user()

    env_optimizer = EnvOptimizer()
    history = env_optimizer.get_optimization_history(env_id)

    return jsonify(history)


@routes.route('/api/env/batch-optimize', methods=['POST'])
@jwt_required()
def batch_optimize_environments():
    current_user = get_current_user()
    if current_user['role'] not in ['admin', 'config', 'dev']:
        return jsonify({'error': 'Permission denied'}), 403

    data = request.get_json()
    env_ids = data.get('env_ids', [])
    custom_goals = data.get('custom_goals')

    optimization_results = []

    from models.environment import Environment
    from models import db

    for env_id in env_ids:
        env = Environment.query.get(env_id)
        if not env:
            optimization_results.append({
                'env_id': env_id,
                'status': 'error',
                'message': 'Environment not found'
            })
            continue

        original_config = json.loads(env.config)

        env_optimizer = EnvOptimizer()
        evaluation_results = env_optimizer.evaluate_environment(original_config)
        optimized_config = env_optimizer.optimize_environment(original_config, evaluation_results, custom_goals)
        optimization_verification = env_optimizer.verify_optimization(original_config, optimized_config)

        env.config = json.dumps(optimized_config)
        env.status = 'optimized'

        from services.env_generator import EnvGenerator
        env_gen = EnvGenerator()
        preview = env_gen.generate_preview(optimized_config)
        env.preview_data = json.dumps(preview)

        env_optimizer.record_optimization(
            env_id=env_id,
            optimizer=current_user['username'],
            trigger='batch',
            original_config=original_config,
            optimized_config=optimized_config,
            scores_before=evaluation_results.get('scores', {}),
            scores_after=optimization_verification.get('optimized_scores', {}),
            improvement=optimization_verification.get('improvement', 0),
            custom_goals=custom_goals
        )

        optimization_results.append({
            'env_id': env_id,
            'status': 'success',
            'original_config': original_config,
            'optimized_config': optimized_config,
            'optimization_verification': optimization_verification
        })

    db.session.commit()

    return jsonify({
        'message': 'Batch optimization completed',
        'results': optimization_results
    })


@routes.route('/api/env/<int:env_id>/visualization', methods=['GET'])
@jwt_required()
def get_env_visualization(env_id):
    current_user = get_current_user()

    from models.environment import Environment
    env = Environment.query.get(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404

    config = json.loads(env.config)

    from models.optimization_record import OptimizationRecord
    from models.adjustment import Adjustment

    opt_records = OptimizationRecord.query.filter_by(env_id=env_id).order_by(OptimizationRecord.created_at.asc()).all()
    adj_records = Adjustment.query.filter_by(env_id=env_id).order_by(Adjustment.created_at.asc()).all()

    score_timeline = []
    for rec in opt_records:
        scores_after = json.loads(rec.scores_after) if rec.scores_after else {}
        score_timeline.append({
            'time': rec.created_at.isoformat(),
            'type': 'optimization',
            'scores': scores_after,
            'improvement': rec.improvement
        })

    for adj in adj_records:
        score_timeline.append({
            'time': adj.created_at.isoformat(),
            'type': 'adjustment',
            'trigger': adj.trigger,
            'reason': adj.reason
        })

    score_timeline.sort(key=lambda x: x['time'])

    env_optimizer = EnvOptimizer()
    current_evaluation = env_optimizer.evaluate_environment(config)

    return jsonify({
        'env_id': env_id,
        'env_name': env.env_name,
        'current_scores': current_evaluation.get('scores', {}),
        'suggestions': current_evaluation.get('suggestions', []),
        'score_timeline': score_timeline,
        'optimization_count': len(opt_records),
        'adjustment_count': len(adj_records)
    })
