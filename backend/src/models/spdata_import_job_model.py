from datetime import datetime

from src.settings.extensions import db


def _iso_utc(value):
    return f"{value.isoformat()}Z" if value else None


class SpdataImportJob(db.Model):
    __tablename__ = "spdata_import_jobs"
    __table_args__ = (
        db.Index("ix_spdata_import_jobs_status_created", "status", "created_at", "id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    rq_job_id = db.Column(db.String(100), unique=True, nullable=True)
    target = db.Column(db.String(30), nullable=False)
    origin = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="QUEUED")
    active_key = db.Column(db.String(64), unique=True, nullable=True)
    requested_by_id = db.Column(
        db.Integer,
        db.ForeignKey("usuarios.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    batch_size = db.Column(db.Integer, nullable=False, default=200)
    attempts = db.Column(db.Integer, nullable=False, default=0)
    max_attempts = db.Column(db.Integer, nullable=False, default=2)
    current_stage = db.Column(db.String(30), nullable=True)
    progress = db.Column(db.JSON, nullable=False, default=dict)
    result = db.Column(db.JSON, nullable=True)
    error_code = db.Column(db.String(100), nullable=True)
    error_message = db.Column(db.Text, nullable=True)
    queued_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, nullable=True)
    heartbeat_at = db.Column(db.DateTime, nullable=True)
    finished_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    requested_by = db.relationship("Usuario", foreign_keys=[requested_by_id])

    @property
    def is_active(self):
        return self.status in {"QUEUED", "RUNNING", "RETRYING"}

    def to_dict(self):
        return {
            "id": self.id,
            "target": self.target,
            "origin": self.origin,
            "status": self.status,
            "current_stage": self.current_stage,
            "attempts": self.attempts,
            "max_attempts": self.max_attempts,
            "batch_size": self.batch_size,
            "progress": self.progress or {},
            "result": self.result,
            "error_code": self.error_code,
            "error_message": self.error_message,
            "requested_by": {
                "id": self.requested_by.id,
                "nome_completo": self.requested_by.nome_completo,
            } if self.requested_by else None,
            "queued_at": _iso_utc(self.queued_at),
            "started_at": _iso_utc(self.started_at),
            "heartbeat_at": _iso_utc(self.heartbeat_at),
            "finished_at": _iso_utc(self.finished_at),
            "created_at": _iso_utc(self.created_at),
            "updated_at": _iso_utc(self.updated_at),
        }
