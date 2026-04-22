from models import db
from datetime import datetime


class Environment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    env_name = db.Column(db.String(100), nullable=False)
    env_id = db.Column(db.String(50), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    config = db.Column(db.Text, nullable=False)
    desc_format = db.Column(db.String(10), default='json')
    status = db.Column(db.String(20), default='created')
    preview_data = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
