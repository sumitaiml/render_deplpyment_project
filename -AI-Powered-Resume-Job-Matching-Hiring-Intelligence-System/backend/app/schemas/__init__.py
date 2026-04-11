"""
Pydantic schemas for request/response validation
Defines data transfer objects for all API endpoints
"""

from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from enum import Enum


class SeniorityLevel(str, Enum):
    """Enum for candidate seniority levels"""
    INTERN = "intern"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"


class ProficiencyLevel(str, Enum):
    """Skill proficiency levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


# ======================== Candidate Schemas ========================

class SkillInfo(BaseModel):
    """Skill information with proficiency"""
    name: str
    proficiency_level: ProficiencyLevel = ProficiencyLevel.INTERMEDIATE
    confidence_score: float = Field(0.5, ge=0.0, le=1.0)
    is_explicit: bool = True
    mentioned_in: Optional[str] = None

    class Config:
        from_attributes = True


class ExperienceEntry(BaseModel):
    """Work experience entry"""
    company: str
    role: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_years: Optional[float] = None
    description: Optional[str] = None
    skills_used: List[str] = []


class EducationEntry(BaseModel):
    """Education entry"""
    institution: str
    degree: str
    field_of_study: Optional[str] = None
    start_year: Optional[int] = None
    end_year: Optional[int] = None
    gpa: Optional[float] = None


class ProjectEntry(BaseModel):
    """Project entry"""
    name: str
    description: Optional[str] = None
    technologies: List[str] = []
    duration: Optional[str] = None
    link: Optional[str] = None


class ResumeUploadRequest(BaseModel):
    """Request for resume upload"""
    file_content: str  # Base64 encoded file or raw text
    file_format: str = "pdf"  # pdf, docx, txt
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    candidate_phone: Optional[str] = None


class ParsedResumeResponse(BaseModel):
    """Response from resume parsing"""
    candidate_id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    years_of_experience: float
    inferred_seniority: SeniorityLevel
    seniority_confidence: float
    skills: List[SkillInfo]
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    projects: List[ProjectEntry]
    extraction_confidence: float
    parse_timestamp: datetime

    class Config:
        from_attributes = True


class CandidateSummary(BaseModel):
    """Summary of a candidate"""
    id: str
    name: str
    email: Optional[str]
    inferred_seniority: SeniorityLevel
    years_of_experience: float
    skills_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateDetail(BaseModel):
    """Detailed candidate information"""
    id: str
    name: str
    email: Optional[str]
    phone: Optional[str]
    inferred_seniority: SeniorityLevel
    seniority_confidence: float
    years_of_experience: float
    skills: List[SkillInfo]
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    projects: List[ProjectEntry]
    created_at: datetime

    class Config:
        from_attributes = True


# ======================== Skill Schemas ========================

class SkillCreateRequest(BaseModel):
    """Request to create a new skill"""
    name: str
    category: Optional[str] = None
    description: Optional[str] = None
    parent_skills: Optional[List[Dict]] = None
    child_skills: Optional[List[Dict]] = None
    related_skills: Optional[List[Dict]] = None


class SkillResponse(BaseModel):
    """Skill response"""
    id: str
    name: str
    category: Optional[str]
    description: Optional[str]
    parent_skills: Optional[List[Dict]]
    child_skills: Optional[List[Dict]]
    related_skills: Optional[List[Dict]]
    created_at: datetime

    class Config:
        from_attributes = True


class SkillGraphResponse(BaseModel):
    """Skill graph relationship"""
    source_skill: str
    target_skill: str
    relationship_type: str
    strength: float


# ======================== Job Schemas ========================

class JobSkillRequirement(BaseModel):
    """Job skill requirement"""
    skill_name: str
    is_required: bool = True
    minimum_proficiency: ProficiencyLevel = ProficiencyLevel.INTERMEDIATE
    importance_score: float = 1.0


class JobCreateRequest(BaseModel):
    """Request to create a job posting"""
    title: str
    description: str
    company: Optional[str] = None
    job_level: Optional[str] = None
    years_of_experience_required: Optional[float] = None
    required_skills: List[Union[JobSkillRequirement, str]] = []
    preferred_skills: List[Union[JobSkillRequirement, str]] = []


class JobResponse(BaseModel):
    """Job response"""
    id: str
    title: str
    description: str
    company: Optional[str]
    job_level: Optional[str]
    years_of_experience_required: Optional[float]
    required_skills_count: int
    preferred_skills_count: int
    created_at: datetime

    class Config:
        from_attributes = True


# ======================== Ranking Schemas ========================

class RankingScores(BaseModel):
    """Individual ranking scores"""
    overall_rank_score: float = Field(..., ge=0, le=100)
    skill_match_score: float = Field(..., ge=0, le=100)
    experience_match_score: float = Field(..., ge=0, le=100)
    seniority_alignment_score: float = Field(..., ge=0, le=100)


class SkillMatchDetail(BaseModel):
    """Skill match detail"""
    skill_name: str
    candidate_has: bool
    candidate_proficiency: Optional[ProficiencyLevel] = None
    required_proficiency: ProficiencyLevel
    is_required: bool


class ExplainabilityData(BaseModel):
    """Explainability data for a ranking"""
    reason: str
    matched_skills: List[str]
    missing_skills: List[str]
    skill_match_details: List[SkillMatchDetail]
    experience_analysis: str
    seniority_reasoning: str
    overall_summary: str


class CandidateRankingResponse(BaseModel):
    """Ranking of a single candidate for a job"""
    ranking_id: str
    candidate_id: str
    candidate_name: str
    candidate_email: Optional[str]
    rank_position: Optional[int]
    overall_rank_score: float
    ranking_scores: RankingScores
    matched_skills: List[str]
    missing_skills: List[str]
    candidate_seniority: SeniorityLevel
    candidate_years_of_experience: float
    explanation: ExplainabilityData
    bias_mitigated: bool
    created_at: datetime

    class Config:
        from_attributes = True


class CandidateRankingRequest(BaseModel):
    """Request to rank candidates for a job"""
    job_id: str
    candidate_ids: Optional[List[str]] = None  # If None, rank all candidates
    apply_bias_mitigation: bool = True
    return_explanations: bool = True


class JobRankingResponse(BaseModel):
    """Final ranked list for a job"""
    job_id: str
    job_title: str
    total_candidates_ranked: int
    rankings: List[CandidateRankingResponse]
    request_timestamp: datetime


# ======================== Seniority Inference Schemas ========================

class SeniorityPredictionResponse(BaseModel):
    """Seniority prediction response"""
    predicted_seniority: SeniorityLevel
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    confidence_reasons: List[str]
    experience_analysis: Dict[str, Any]
    skill_analysis: Dict[str, Any]
    role_progression_analysis: List[str]


# ======================== Explainability Schemas ========================

class ExplainabilityRequest(BaseModel):
    """Request for explainability details"""
    ranking_id: str


# ======================== Analytics Schemas ========================

class RankingMetrics(BaseModel):
    """Ranking performance metrics"""
    ndcg_score: float
    map_score: float
    precision_at_k: float
    recruiter_satisfaction: Optional[float] = None


class BiasMetrics(BaseModel):
    """Bias reduction metrics"""
    demographic_parity_difference: float
    equal_opportunity_difference: float
    fairness_score: float


# ======================== Pagination ========================

class PaginationParams(BaseModel):
    """Pagination parameters"""
    skip: int = 0
    limit: int = 10
    
    class Config:
        json_schema_extra = {
            "example": {
                "skip": 0,
                "limit": 20
            }
        }
