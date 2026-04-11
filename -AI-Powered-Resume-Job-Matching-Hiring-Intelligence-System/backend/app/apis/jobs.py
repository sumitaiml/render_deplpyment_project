"""
Job API Endpoints
Handles job postings and skill requirements management
"""

import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.schemas import (
    JobCreateRequest,
    JobResponse,
    JobSkillRequirement
)
from app.models import Job as JobModel, Skill, JobSkill as JobSkillModel
from app.core import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["Jobs"])


def _normalize_skill_list(skill_list):
    normalized = []
    for item in skill_list or []:
        if isinstance(item, JobSkillRequirement):
            normalized.append(item)
        elif isinstance(item, str):
            normalized.append(JobSkillRequirement(skill_name=item))
        elif isinstance(item, dict):
            normalized.append(JobSkillRequirement(**item))
    return normalized


@router.post("/create", response_model=JobResponse)
async def create_job(
    request: JobCreateRequest,
    db: Session = Depends(get_db)
):
    """Create a new job posting"""
    try:
        job = JobModel(
            id=str(uuid.uuid4()),
            title=request.title,
            description=request.description,
            company=request.company,
            job_level=request.job_level,
            years_of_experience_required=request.years_of_experience_required,
            parsed_description={'description': request.description}
        )
        
        db.add(job)
        db.flush()
        
        # Add required skills
        for skill_req in _normalize_skill_list(request.required_skills):
            skill = db.query(Skill).filter(Skill.name == skill_req.skill_name).first()
            if not skill:
                skill = Skill(
                    id=str(uuid.uuid4()),
                    name=skill_req.skill_name
                )
                db.add(skill)
                db.flush()
            
            job_skill = JobSkillModel(
                id=str(uuid.uuid4()),
                job_id=job.id,
                skill_id=skill.id,
                is_required=True,
                minimum_proficiency=skill_req.minimum_proficiency,
                importance_score=skill_req.importance_score
            )
            db.add(job_skill)
        
        # Add preferred skills
        for skill_req in _normalize_skill_list(request.preferred_skills):
            skill = db.query(Skill).filter(Skill.name == skill_req.skill_name).first()
            if not skill:
                skill = Skill(
                    id=str(uuid.uuid4()),
                    name=skill_req.skill_name
                )
                db.add(skill)
                db.flush()
            
            job_skill = JobSkillModel(
                id=str(uuid.uuid4()),
                job_id=job.id,
                skill_id=skill.id,
                is_required=False,
                minimum_proficiency=skill_req.minimum_proficiency,
                importance_score=skill_req.importance_score
            )
            db.add(job_skill)
        
        db.commit()
        
        return JobResponse(
            id=job.id,
            title=job.title,
            description=job.description,
            company=job.company,
            job_level=job.job_level,
            years_of_experience_required=job.years_of_experience_required,
            required_skills_count=len(request.required_skills),
            preferred_skills_count=len(request.preferred_skills),
            created_at=job.created_at
        )
    
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=list[JobResponse])
async def list_jobs(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """List all jobs with pagination"""
    try:
        jobs = db.query(JobModel).offset(skip).limit(limit).all()
        
        return [
            JobResponse(
                id=j.id,
                title=j.title,
                description=j.description,
                company=j.company,
                job_level=j.job_level,
                years_of_experience_required=j.years_of_experience_required,
                required_skills_count=sum(1 for s in j.job_skills if s.is_required),
                preferred_skills_count=sum(1 for s in j.job_skills if not s.is_required),
                created_at=j.created_at
            )
            for j in jobs
        ]
    
    except Exception as e:
        logger.error(f"Error listing jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{job_id}", response_model=dict)
async def get_job_details(job_id: str, db: Session = Depends(get_db)):
    """Get detailed job information including required and preferred skills"""
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        required_skills = [
            {
                'skill_id': js.skill.id,
                'skill': js.skill.name,
                'is_required': True,
                'importance_score': js.importance_score
            }
            for js in job.job_skills if js.is_required
        ]
        
        preferred_skills = [
            {
                'skill_id': js.skill.id,
                'skill': js.skill.name,
                'is_required': False,
                'importance_score': js.importance_score
            }
            for js in job.job_skills if not js.is_required
        ]
        
        return {
            'id': job.id,
            'title': job.title,
            'description': job.description,
            'company': job.company,
            'job_level': job.job_level,
            'years_of_experience_required': job.years_of_experience_required,
            'required_skills': required_skills,
            'preferred_skills': preferred_skills,
            'created_at': job.created_at
        }
    
    except Exception as e:
        logger.error(f"Error fetching job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{job_id}")
@router.delete("/delete_job/{job_id}")
async def delete_job(job_id: str, db: Session = Depends(get_db)):
    """Delete a job by ID."""
    try:
        job = db.query(JobModel).filter(JobModel.id == job_id).first()

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        db.delete(job)
        db.commit()

        return {
            "success": True,
            "message": "Job deleted successfully",
            "job_id": job_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
