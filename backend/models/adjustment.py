from models import db
from datetime import datetime


class Adjustment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    env_id = db.Column(db.Integer, db.ForeignKey('environment.id'), nullable=False)
    adjuster = db.Column(db.String(50), nullable=False)
    trigger = db.Column(db.String(50), nullable=False)
    params = db.Column(db.Text, nullable=False)
    reason = db.Column(db.Text)
    performance_before = db.Column(db.Text)
    performance_after = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
