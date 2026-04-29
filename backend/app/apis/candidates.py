"""
Candidate API Endpoints
Handles candidate resume uploads, profile management, and seniority inference
"""

import logging
import mimetypes
from datetime import datetime
from typing import Optional
import uuid
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form, Response
from sqlalchemy import asc, desc, or_
from sqlalchemy.orm import Session

from app.schemas import (
    ResumeUploadRequest,
    ParsedResumeResponse,
    CandidateSummary,
    CandidateDetail,
    SkillInfo,
    SeniorityLevel as SeniorityEnum
)
from app.core import get_db, settings
from app.models import (
    Candidate as CandidateModel,
    Skill,
    CandidateSkill,
    SeniorityLevel
)
from app.services import (
    ResumeParser,
    SkillExtractor,
    SeniorityInference
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/candidates", tags=["Candidates"])

@lru_cache(maxsize=1)
def get_resume_parser() -> ResumeParser:
    return ResumeParser()


@lru_cache(maxsize=1)
def get_skill_extractor() -> SkillExtractor:
    return SkillExtractor()


@lru_cache(maxsize=1)
def get_seniority_inference() -> SeniorityInference:
    return SeniorityInference()


@router.post("/upload-resume", response_model=ParsedResumeResponse)
async def upload_resume(
    name: str = Form(...),
    email: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload and parse a resume
    Extracts: Name, Email, Experience, Education, Skills, Seniority
    """
    try:
        allowed_extensions = set(settings.ALLOWED_RESUME_FORMATS)
        file_ext = file.filename.split('.')[-1].lower() if file.filename and '.' in file.filename else 'txt'
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported resume format: {file_ext}. Allowed formats: {', '.join(sorted(allowed_extensions))}"
            )

        # Read and process file
        content = await file.read()
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"Resume file exceeds maximum size of {settings.MAX_FILE_SIZE // (1024 * 1024)} MB"
            )
        
        # Determine file format from filename
        file_format = 'pdf' if file_ext == 'pdf' else ('docx' if file_ext in ['docx', 'doc'] else 'txt')
        
        # Parse resume
        parsed = get_resume_parser().parse_resume(
            content,
            file_format,
            name
        )
        
        if not parsed['success']:
            raise HTTPException(status_code=400, detail=f"Parse failed: {parsed['error']}")
        
        # Extract skills
        try:
            skills_result = get_skill_extractor().extract_all_skills(parsed)
            parsed['skills'] = skills_result['all_skills']
            if not parsed['skills']:
                parsed['skills'] = []
        except Exception as e:
            logger.warning(f"Skill extraction failed: {e}")
            parsed['skills'] = []
        
        # Infer seniority
        try:
            seniority_result = get_seniority_inference().infer_seniority(parsed)
            # Map seniority levels to valid enum values
            seniority_mapping = {
                'Intern': 'intern',
                'Junior': 'junior',
                'Mid': 'mid_level',
                'Senior': 'senior',
                'Lead': 'lead',
                'intern': 'intern',
                'junior': 'junior',
                'mid': 'mid_level',
                'mid_level': 'mid_level',
                'senior': 'senior',
                'lead': 'lead'
            }
            seniority_str = seniority_result.get('predicted_seniority', 'Mid')
            mapped_seniority = seniority_mapping.get(str(seniority_str), 'mid_level')
        except Exception as e:
            logger.warning(f"Seniority inference failed: {e}")
            seniority_result = {
                'predicted_seniority': 'mid_level',
                'confidence_score': 0.5
            }
            mapped_seniority = 'mid_level'
        
        # Create candidate in database
        try:
            candidate = CandidateModel(
                id=str(uuid.uuid4()),
                name=parsed.get('name', 'Unknown'),
                email=email,
                phone=parsed.get('phone', ''),
                resume_text=parsed.get('resume_text', ''),
                years_of_experience=float(parsed.get('years_of_experience', 0)),
                inferred_seniority=mapped_seniority,  # Use mapped seniority value
                seniority_confidence=float(seniority_result.get('confidence_score', 0.5)),
                parsed_experience=parsed.get('experience', []),
                parsed_education=parsed.get('education', []),
                parsed_projects=parsed.get('projects', []),
            )
            
            db.add(candidate)
            db.flush()

            uploads_dir = Path(settings.UPLOAD_DIR).resolve() / "resumes"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            stored_resume_path = uploads_dir / f"{candidate.id}.{file_ext}"
            stored_resume_path.write_bytes(content)
            candidate.resume_file_path = str(stored_resume_path)
            db.flush()
        except Exception as e:
            logger.error(f"Failed to create candidate: {e}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
        
        # Add skills to database
        try:
            for skill_data in parsed.get('skills', []):
                try:
                    skill_name = skill_data.get('skill', 'Unknown')
                    
                    # Find or create skill
                    skill = db.query(Skill).filter(Skill.name == skill_name).first()
                    if not skill:
                        skill = Skill(
                            id=str(uuid.uuid4()),
                            name=skill_name,
                            category=skill_data.get('category', 'General')
                        )
                        db.add(skill)
                        db.flush()
                    
                    # Add candidate-skill relationship
                    candidate_skill = CandidateSkill(
                        id=str(uuid.uuid4()),
                        candidate_id=candidate.id,
                        skill_id=skill.id,
                        proficiency_level=skill_data.get('proficiency_level', 'intermediate'),
                        confidence_score=float(skill_data.get('confidence_score', 0.5)),
                        is_explicit=skill_data.get('is_explicit', True),
                        mentioned_in=skill_data.get('mentioned_in', 'resume'),
                        extraction_context=skill_data.get('mentioned_in', '')
                    )
                    db.add(candidate_skill)
                except Exception as e:
                    logger.warning(f"Failed to add skill {skill_data}: {e}")
                    continue
            
            db.commit()
        except Exception as e:
            logger.error(f"Failed to add skills: {e}")
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Skills database error: {str(e)}")
        
        # Return response
        try:
            # Build skills list safely
            skills_list = []
            for s in parsed.get('skills', [])[:10]:
                try:
                    skills_list.append(
                        SkillInfo(
                            name=str(s.get('skill', 'Unknown')),
                            proficiency_level=str(s.get('proficiency_level', 'intermediate')),
                            confidence_score=float(s.get('confidence_score', 0.5)),
                            is_explicit=bool(s.get('is_explicit', True)),
                            mentioned_in=str(s.get('mentioned_in', 'resume'))
                        )
                    )
                except Exception as e:
                    logger.warning(f"Failed to build skill info: {e}")
                    continue
            
            return ParsedResumeResponse(
                candidate_id=candidate.id,
                name=str(candidate.name),
                email=str(candidate.email) if candidate.email else None,
                phone=str(candidate.phone) if candidate.phone else None,
                years_of_experience=float(candidate.years_of_experience or 0),
                inferred_seniority=SeniorityEnum(mapped_seniority),
                seniority_confidence=float(candidate.seniority_confidence or 0.5),
                skills=skills_list,
                experience=parsed.get('experience', [])[:5],
                education=parsed.get('education', [])[:3],
                projects=parsed.get('projects', [])[:3],
                extraction_confidence=float(parsed.get('extraction_confidence', 0.5)),
                parse_timestamp=parsed.get('parse_timestamp', datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Failed to build response: {e}")
            raise HTTPException(status_code=500, detail=f"Response build error: {str(e)}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Resume upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}/resume")
async def get_candidate_resume(
    candidate_id: str,
    download: bool = False,
    db: Session = Depends(get_db)
):
    """View or download the original uploaded resume for a candidate."""
    try:
        candidate = db.query(CandidateModel).filter(CandidateModel.id == candidate_id).first()

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        safe_name = (candidate.name or "candidate").strip().replace(" ", "_") or "candidate"
        stored_path = Path(candidate.resume_file_path) if candidate.resume_file_path else None

        if stored_path and stored_path.exists():
            content = stored_path.read_bytes()
            media_type = mimetypes.guess_type(stored_path.name)[0] or "application/octet-stream"
            filename = stored_path.name
        else:
            resume_text = candidate.resume_text or "Resume not available for this candidate."
            content = resume_text.encode("utf-8")
            media_type = "text/plain; charset=utf-8"
            filename = f"{safe_name}_resume.txt"

        disposition = "attachment" if download else "inline"
        headers = {
            "Content-Disposition": f'{disposition}; filename="{filename}"'
        }

        return Response(content=content, media_type=media_type, headers=headers)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resume for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}/resume-text")
async def get_candidate_resume_text(
    candidate_id: str,
    db: Session = Depends(get_db)
):
    """Return the parsed resume text for highlighting and evidence display"""
    try:
        candidate = db.query(CandidateModel).filter(CandidateModel.id == candidate_id).first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        resume_text = candidate.resume_text or ""
        return {"resume_text": resume_text}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching resume text for candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/list", response_model=list[CandidateSummary])
async def list_candidates(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    seniority: Optional[str] = None,
    min_years_experience: Optional[float] = None,
    max_years_experience: Optional[float] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db)
):
    """List all candidates with pagination"""
    try:
        query = db.query(CandidateModel)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    CandidateModel.name.ilike(search_term),
                    CandidateModel.email.ilike(search_term),
                    CandidateModel.phone.ilike(search_term),
                )
            )

        if seniority:
            seniority_value = seniority.strip().lower()
            valid_seniorities = {level.value for level in SeniorityLevel}
            if seniority_value not in valid_seniorities:
                raise HTTPException(status_code=400, detail=f"Invalid seniority filter: {seniority}")
            query = query.filter(CandidateModel.inferred_seniority == SeniorityLevel(seniority_value))

        if min_years_experience is not None:
            query = query.filter(CandidateModel.years_of_experience >= min_years_experience)

        if max_years_experience is not None:
            query = query.filter(CandidateModel.years_of_experience <= max_years_experience)

        sort_map = {
            "created_at": CandidateModel.created_at,
            "name": CandidateModel.name,
            "years_of_experience": CandidateModel.years_of_experience,
        }

        sort_key = sort_by.strip().lower()
        if sort_key not in sort_map:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sort_by value: {sort_by}. Allowed: {', '.join(sort_map.keys())}"
            )

        sort_direction = sort_order.strip().lower()
        if sort_direction not in {"asc", "desc"}:
            raise HTTPException(status_code=400, detail="sort_order must be 'asc' or 'desc'")

        query = query.order_by(asc(sort_map[sort_key]) if sort_direction == "asc" else desc(sort_map[sort_key]))
        candidates = query.offset(skip).limit(limit).all()
        
        return [
            CandidateSummary(
                id=c.id,
                name=c.name,
                email=c.email,
                inferred_seniority=SeniorityEnum(c.inferred_seniority),
                years_of_experience=c.years_of_experience,
                skills_count=len(c.candidate_skills),
                created_at=c.created_at
            )
            for c in candidates
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{candidate_id}", response_model=CandidateDetail)
async def get_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Get detailed candidate information"""
    try:
        candidate = db.query(CandidateModel).filter(CandidateModel.id == candidate_id).first()
        
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        
        skills = [
            SkillInfo(
                name=cs.skill.name,
                proficiency_level=cs.proficiency_level,
                confidence_score=cs.confidence_score,
                is_explicit=cs.is_explicit,
                mentioned_in=cs.mentioned_in
            )
            for cs in candidate.candidate_skills
        ]
        
        return CandidateDetail(
            id=candidate.id,
            name=candidate.name,
            email=candidate.email,
            phone=candidate.phone,
            inferred_seniority=SeniorityEnum(candidate.inferred_seniority),
            seniority_confidence=candidate.seniority_confidence,
            years_of_experience=candidate.years_of_experience,
            skills=skills,
            experience=candidate.parsed_experience or [],
            education=candidate.parsed_education or [],
            projects=candidate.parsed_projects or [],
            created_at=candidate.created_at
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching candidate: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{candidate_id}")
@router.delete("/delete_candidate/{candidate_id}")
async def delete_candidate(candidate_id: str, db: Session = Depends(get_db)):
    """Delete a candidate by ID."""
    try:
        candidate = db.query(CandidateModel).filter(CandidateModel.id == candidate_id).first()

        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")

        db.delete(candidate)
        db.commit()

        return {
            "success": True,
            "message": "Candidate deleted successfully",
            "candidate_id": candidate_id,
        }
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting candidate {candidate_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
