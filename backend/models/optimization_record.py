from models import db
from datetime import datetime


class OptimizationRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    env_id = db.Column(db.Integer, db.ForeignKey('environment.id'), nullable=False)
    optimizer = db.Column(db.String(50), nullable=False)
    trigger = db.Column(db.String(50), nullable=False)
    original_config = db.Column(db.Text)
    optimized_config = db.Column(db.Text)
    scores_before = db.Column(db.Text)
    scores_after = db.Column(db.Text)
    improvement = db.Column(db.Float)
    custom_goals = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
