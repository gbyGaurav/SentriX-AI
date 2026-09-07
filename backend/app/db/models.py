from sqlalchemy import Column, String, Integer, Float, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.db.database import Base

class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    input_type = Column(String, nullable=False)
    risk_score = Column(Integer, nullable=False)
    risk_level = Column(String, nullable=False)
    fraud_types = Column(JSON, nullable=False)
    confidence = Column(Float, nullable=False)
    explanation = Column(String, nullable=False)
    recommendations = Column(JSON, nullable=False)
    extracted_content = Column(JSON, nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    detectors = relationship("DetectorResultDB", back_populates="analysis")
    evidences = relationship("EvidenceDB", back_populates="analysis")

class DetectorResultDB(Base):
    __tablename__ = 'detector_results'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey('analyses.id'), index=True)
    module = Column(String, nullable=False)
    fraud_probability = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    risk = Column(String, nullable=False)
    signals = Column(JSON, nullable=False)
    model_version = Column(String, nullable=False)
    processing_time_ms = Column(Float, nullable=False)
    metadata_ = Column(JSON, nullable=False)
    
    analysis = relationship("Analysis", back_populates="detectors")

class EvidenceDB(Base):
    __tablename__ = 'evidences'
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_id = Column(String, ForeignKey('analyses.id'), index=True)
    evidence_type = Column(String, nullable=False)
    source_modality = Column(String, nullable=False)
    target_modality = Column(String, nullable=True)
    content = Column(String, nullable=False)
    severity = Column(String, nullable=False)
    evidence_relationship = Column(String, nullable=True)
    
    analysis = relationship("Analysis", back_populates="evidences")
