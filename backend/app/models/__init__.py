"""
Database Models for HRTech Platform
Defines all entities for resume, skills, candidates, jobs, and rankings
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, 
    ForeignKey, Boolean, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from enum import Enum as PyEnum
import uuid

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), nullable=False, unique=True, index=True)
    username = Column(String(100), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class SeniorityLevel(str, PyEnum):
    """Enum for candidate seniority levels"""
    INTERN = "intern"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"


class Candidate(Base):
    """Candidate model - represents a job applicant"""
    __tablename__ = "candidates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=True, unique=True)
    phone = Column(String(20), nullable=True)
    
    # Resume data
    resume_text = Column(Text, nullable=True)
    resume_file_path = Column(String(500), nullable=True)
    
    # Extracted information
    years_of_experience = Column(Float, nullable=True)
    education_level = Column(String(100), nullable=True)  # e.g., "B.Tech", "M.Tech"
    
    # Seniority
    inferred_seniority = Column(SQLEnum(SeniorityLevel), nullable=True)
    seniority_confidence = Column(Float, default=0.0)
    
    # Parsed data (JSON for flexibility)
    parsed_experience = Column(JSON, nullable=True)  # [{company, role, duration, ...}]
    parsed_education = Column(JSON, nullable=True)   # [{school, degree, year, ...}]
    parsed_projects = Column(JSON, nullable=True)    # [{name, description, skills, ...}]
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate_skills = relationship("CandidateSkill", back_populates="candidate", cascade="all, delete-orphan")
    candidate_rankings = relationship("CandidateRanking", back_populates="candidate", cascade="all, delete-orphan")


class Skill(Base):
    """Skill ontology - normalized skills in the system"""
    __tablename__ = "skills"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False, unique=True, index=True)
    category = Column(String(100), nullable=True)  # e.g., "Programming", "Database", "Cloud"
    description = Column(Text, nullable=True)
    
    # Skill graph relationships
    parent_skills = Column(JSON, nullable=True)      # [{skill_id, relationship_type}]
    child_skills = Column(JSON, nullable=True)       # [{skill_id, relationship_type}]
    related_skills = Column(JSON, nullable=True)     # [{skill_id, similarity_score}]
    
    # Embeddings for semantic matching
    embedding = Column(JSON, nullable=True)  # Store embeddings as JSON
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate_skills = relationship("CandidateSkill", back_populates="skill", cascade="all, delete-orphan")
    job_skills = relationship("JobSkill", back_populates="skill", cascade="all, delete-orphan")


class CandidateSkill(Base):
    """Junction table: Candidate-Skill relationship with proficiency levels"""
    __tablename__ = "candidate_skills"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False, index=True)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False, index=True)
    
    # Proficiency and confidence
    proficiency_level = Column(String(50), default="intermediate")  # beginner, intermediate, advanced, expert
    confidence_score = Column(Float, default=0.5)  # 0-1 confidence the candidate has this skill
    is_explicit = Column(Boolean, default=True)     # True if mentioned directly, False if inferred
    
    # Context (where skill was extracted from)
    mentioned_in = Column(String(100), nullable=True)  # "experience", "project", "education", "inferred"
    extraction_context = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="candidate_skills")
    skill = relationship("Skill", back_populates="candidate_skills")


class Job(Base):
    """Job posting model"""
    __tablename__ = "jobs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=False)
    company = Column(String(255), nullable=True)
    job_level = Column(String(50), nullable=True)  # e.g., "senior", "junior"
    years_of_experience_required = Column(Float, nullable=True)
    
    # Parsed job data
    parsed_description = Column(JSON, nullable=True)
    required_skills_json = Column(JSON, nullable=True)
    preferred_skills_json = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    job_skills = relationship("JobSkill", back_populates="job", cascade="all, delete-orphan")
    rankings = relationship("CandidateRanking", back_populates="job", cascade="all, delete-orphan")


class JobSkill(Base):
    """Junction table: Job-Skill requirements"""
    __tablename__ = "job_skills"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False, index=True)
    skill_id = Column(String(36), ForeignKey("skills.id"), nullable=False, index=True)
    
    # Requirement level
    is_required = Column(Boolean, default=True)     # True if required, False if preferred
    minimum_proficiency = Column(String(50), default="intermediate")
    importance_score = Column(Float, default=1.0)  # Weight for this skill in the job
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    job = relationship("Job", back_populates="job_skills")
    skill = relationship("Skill", back_populates="job_skills")


class CandidateRanking(Base):
    """Ranking model - final ranking of candidates for a job"""
    __tablename__ = "candidate_rankings"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    job_id = Column(String(36), ForeignKey("jobs.id"), nullable=False, index=True)
    candidate_id = Column(String(36), ForeignKey("candidates.id"), nullable=False, index=True)
    
    # Ranking scores
    overall_rank_score = Column(Float, nullable=False)  # 0-100
    skill_match_score = Column(Float, nullable=False)   # 0-100
    experience_match_score = Column(Float, nullable=False)  # 0-100
    seniority_alignment_score = Column(Float, nullable=False)  # 0-100
    
    # Ranking position
    rank_position = Column(Integer, nullable=True)
    percentile = Column(Float, nullable=True)
    
    # Quality metrics
    matched_skills_count = Column(Integer, default=0)
    missing_skills_count = Column(Integer, default=0)
    years_of_exp_match = Column(Float, nullable=True)
    
    # Explainability data (stored as JSON for flexibility)
    explanation = Column(JSON, nullable=True)  # {reason, matched_skills, missing_skills, etc.}
    
    # Whether bias mitigation was applied
    bias_mitigated = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    candidate = relationship("Candidate", back_populates="candidate_rankings")
    job = relationship("Job", back_populates="rankings")


class SkillGraph(Base):
    """Skill Graph - relationships between skills for inference"""
    __tablename__ = "skill_graphs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    source_skill_id = Column(String(255), nullable=False, index=True)
    target_skill_id = Column(String(255), nullable=False, index=True)
    relationship_type = Column(String(50), nullable=False)  # "requires", "related_to", "implies"
    strength = Column(Float, default=0.5)  # 0-1, strength of relationship
    
    # Example: Spring Boot --requires--> Java
    # Example: Python --related_to--> R (0.8)
    # Example: REST APIs --implies--> HTTP (0.9)


class SeniorityModel(Base):
    """Stored seniority inference model metadata"""
    __tablename__ = "seniority_models"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_version = Column(String(50), nullable=False, unique=True)
    model_type = Column(String(100), nullable=False)  # e.g., "gradient_boosting", "neural_net"
    model_path = Column(String(500), nullable=False)
    feature_set = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)
    
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class RankingModel(Base):
    """Stored ranking model metadata"""
    __tablename__ = "ranking_models"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    model_version = Column(String(50), nullable=False, unique=True)
    model_type = Column(String(100), nullable=False)  # e.g., "xgboost", "lightgbm", "neural_ranker"
    model_path = Column(String(500), nullable=False)
    feature_set = Column(JSON, nullable=True)
    performance_metrics = Column(JSON, nullable=True)  # {ndcg, map, precision_at_k}
    
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AuditLog(Base):
    """Audit trail for recruiter actions and system decisions"""
    __tablename__ = "audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    action = Column(String(255), nullable=False)
    entity_type = Column(String(100), nullable=False)  # "candidate", "job", "ranking"
    entity_id = Column(String(36), nullable=True)
    details = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
