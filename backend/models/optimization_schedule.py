from models import db
from datetime import datetime


class OptimizationSchedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    env_id = db.Column(db.Integer, db.ForeignKey('environment.id'), nullable=False)
    interval = db.Column(db.String(20), nullable=False, default='daily')
    enabled = db.Column(db.Boolean, default=True)
    last_run = db.Column(db.DateTime)
    next_run = db.Column(db.DateTime)
    custom_goals = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
