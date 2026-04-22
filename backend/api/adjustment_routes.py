from api import routes, get_current_user
from flask import request, jsonify
from models import db
from models.adjustment import Adjustment
from flask_jwt_extended import jwt_required
import json


@routes.route('/api/adjustments', methods=['GET'])
@jwt_required()
def get_adjustments():
    current_user = get_current_user()
    env_id = request.args.get('env_id')
    
    query = Adjustment.query
    if env_id:
        query = query.filter_by(env_id=env_id)
    
    adjustments = query.order_by(Adjustment.created_at.desc()).all()
    
    return jsonify([{
        'id': adj.id,
        'env_id': adj.env_id,
        'adjuster': adj.adjuster,
        'trigger': adj.trigger,
        'params': json.loads(adj.params),
        'reason': adj.reason,
        'performance_before': json.loads(adj.performance_before) if adj.performance_before else None,
        'performance_after': json.loads(adj.performance_after) if adj.performance_after else None,
        'created_at': adj.created_at.isoformat()
    } for adj in adjustments])


@routes.route('/api/adjustments/<int:adj_id>', methods=['GET'])
@jwt_required()
def get_adjustment(adj_id):
    current_user = get_current_user()
    adjustment = Adjustment.query.get(adj_id)
    
    if not adjustment:
        return jsonify({'error': 'Adjustment not found'}), 404
    
    return jsonify({
        'id': adjustment.id,
        'env_id': adjustment.env_id,
        'adjuster': adjustment.adjuster,
        'trigger': adjustment.trigger,
        'params': json.loads(adjustment.params),
        'reason': adjustment.reason,
        'performance_before': json.loads(adjustment.performance_before) if adjustment.performance_before else None,
        'performance_after': json.loads(adjustment.performance_after) if adjustment.performance_after else None,
        'created_at': adjustment.created_at.isoformat()
    })


@routes.route('/api/environments/<int:env_id>/adjustments', methods=['GET'])
@jwt_required()
def get_environment_adjustments(env_id):
    current_user = get_current_user()
    adjustments = Adjustment.query.filter_by(env_id=env_id).order_by(Adjustment.created_at.desc()).all()
    
    return jsonify([{
        'id': adj.id,
        'adjuster': adj.adjuster,
        'trigger': adj.trigger,
        'params': json.loads(adj.params),
        'reason': adj.reason,
        'created_at': adj.created_at.isoformat()
    } for adj in adjustments])
