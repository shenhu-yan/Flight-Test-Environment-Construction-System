from models import db
from datetime import datetime


class Model(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    model_name = db.Column(db.String(100), nullable=False)
    model_id = db.Column(db.String(100), unique=True, nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)
    task_id = db.Column(db.String(50), nullable=False)
    model_type = db.Column(db.String(50), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
