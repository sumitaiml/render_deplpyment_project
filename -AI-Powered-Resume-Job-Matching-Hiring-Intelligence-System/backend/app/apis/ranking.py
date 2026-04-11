"""
Ranking & Explanation API Endpoints
Handles candidate ranking against jobs and explainability
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import uuid

from app.schemas import (
    CandidateRankingRequest,
    JobRankingResponse,
    CandidateRankingResponse,
    RankingScores,
    ExplainabilityData,
    SkillMatchDetail,
    ProficiencyLevel,
    SeniorityLevel as SeniorityEnum
)
from app.models import (
    Candidate as CandidateModel,
    Job as JobModel,
    CandidateRanking,
    JobSkill as JobSkillModel,
    SeniorityLevel
)
from app.core import get_db
from app.services import RankingModel, ExplainabilityEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ranking", tags=["Ranking"])

# Initialize services
ranking_model = RankingModel()
explainability_engine = ExplainabilityEngine()


@router.post("/rank-candidates")
async def rank_candidates(
    request: CandidateRankingRequest,
    db: Session = Depends(get_db)
):
    """
    Rank candidates against a job
    Optionally returns explainability for each candidate
    """
    try:
        # Get job
        job = db.query(JobModel).filter(JobModel.id == request.job_id).first()
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get required and preferred skills
        job_skills = db.query(JobSkillModel).filter(JobSkillModel.job_id == request.job_id).all()
        
        required_skills = [
            {
                'skill': js.skill.name,
                'proficiency': js.minimum_proficiency
            }
            for js in job_skills if js.is_required
        ]
        
        preferred_skills = [
            {
                'skill': js.skill.name,
                'proficiency': js.minimum_proficiency
            }
            for js in job_skills if not js.is_required
        ]
        
        # Get candidates
        if request.candidate_ids:
            candidates = db.query(CandidateModel).filter(
                CandidateModel.id.in_(request.candidate_ids)
            ).all()
        else:
            candidates = db.query(CandidateModel).all()
        
        if not candidates:
            raise HTTPException(status_code=400, detail="No candidates found")
        
        # Prepare candidate data for ranking
        candidate_data_list = []
        for candidate in candidates:
            skills = [
                {
                    'skill': cs.skill.name,
                    'proficiency_level': cs.proficiency_level,
                    'is_explicit': cs.is_explicit
                }
                for cs in candidate.candidate_skills
            ]
            
            candidate_data_list.append({
                'id': candidate.id,
                'name': candidate.name,
                'years_of_experience': candidate.years_of_experience,
                'inferred_seniority': candidate.inferred_seniority.value,
                'skills': skills
            })
        
        job_data = {
            'title': job.title,
            'job_level': job.job_level,
            'years_of_experience_required': job.years_of_experience_required,
            'required_skills': required_skills,
            'preferred_skills': preferred_skills
        }
        
        # Rank candidates
        rankings = ranking_model.rank_candidates(candidate_data_list, job_data)
        
        # Generate explanations if requested
        responses = []
        for ranking in rankings:
            candidate = next((c for c in candidates if c.id == ranking['candidate_id']), None)
            
            if not candidate:
                continue
            
            # Generate explanation
            if request.return_explanations:
                explanation_data = explainability_engine.generate_ranking_explanation(
                    {
                        'id': candidate.id,
                        'name': candidate.name,
                        'years_of_experience': candidate.years_of_experience,
                        'inferred_seniority': candidate.inferred_seniority.value,
                        'skills': [cs.skill.name for cs in candidate.candidate_skills]
                    },
                    job_data,
                    ranking
                )
            else:
                explanation_data = None
            
            # Save ranking to database
            candidate_ranking = CandidateRanking(
                id=str(uuid.uuid4()),
                job_id=request.job_id,
                candidate_id=ranking['candidate_id'],
                overall_rank_score=ranking['overall_rank_score'],
                skill_match_score=ranking['skill_match_score'],
                experience_match_score=ranking['experience_match_score'],
                seniority_alignment_score=ranking['seniority_alignment_score'],
                rank_position=ranking['rank_position'],
                percentile=ranking['percentile'],
                matched_skills_count=ranking['matched_skills_count'],
                missing_skills_count=ranking['missing_skills_count'],
                explanation=explanation_data if request.return_explanations else None,
                bias_mitigated=request.apply_bias_mitigation
            )
            db.add(candidate_ranking)
            
            # Build response
            if explanation_data:
                skill_match_details = []
                for skill_name in explanation_data.get('matched_skills', []):
                    skill_match_details.append(
                        SkillMatchDetail(
                            skill_name=skill_name,
                            candidate_has=True,
                            candidate_proficiency=None,
                            required_proficiency=ProficiencyLevel.INTERMEDIATE,
                            is_required=True
                        )
                    )
                for skill_name in explanation_data.get('missing_skills', []):
                    skill_match_details.append(
                        SkillMatchDetail(
                            skill_name=skill_name,
                            candidate_has=False,
                            candidate_proficiency=None,
                            required_proficiency=ProficiencyLevel.INTERMEDIATE,
                            is_required=True
                        )
                    )

                explanation_response = ExplainabilityData(
                    reason=explanation_data['reason'],
                    matched_skills=explanation_data['matched_skills'],
                    missing_skills=explanation_data['missing_skills'],
                    skill_match_details=skill_match_details,
                    experience_analysis=explanation_data['experience_analysis'],
                    seniority_reasoning=explanation_data['seniority_reasoning'],
                    overall_summary=explanation_data['overall_summary']
                )
            else:
                explanation_response = None
            
            response = CandidateRankingResponse(
                ranking_id=candidate_ranking.id,
                candidate_id=ranking['candidate_id'],
                candidate_name=ranking['candidate_name'],
                candidate_email=candidate.email,
                rank_position=ranking['rank_position'],
                overall_rank_score=ranking['overall_rank_score'],
                ranking_scores=RankingScores(
                    overall_rank_score=ranking['overall_rank_score'],
                    skill_match_score=ranking['skill_match_score'],
                    experience_match_score=ranking['experience_match_score'],
                    seniority_alignment_score=ranking['seniority_alignment_score']
                ),
                matched_skills=ranking['matched_skills'],
                missing_skills=ranking['missing_skills'],
                candidate_seniority=SeniorityEnum(ranking['candidate_seniority']),
                candidate_years_of_experience=ranking['years_of_exp_match'],
                explanation=explanation_response,
                bias_mitigated=request.apply_bias_mitigation,
                created_at=ranking.get('created_at') or candidate_ranking.created_at or datetime.utcnow()
            )
            responses.append(response)
        
        db.commit()
        
        return JobRankingResponse(
            job_id=request.job_id,
            job_title=job.title,
            total_candidates_ranked=len(responses),
            rankings=responses,
            request_timestamp=datetime.utcnow()
        )
    
    except Exception as e:
        logger.error(f"Error ranking candidates: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings/{job_id}")
async def get_job_rankings(job_id: str, db: Session = Depends(get_db)):
    """Get all rankings for a specific job"""
    try:
        rankings = db.query(CandidateRanking).filter(
            CandidateRanking.job_id == job_id
        ).order_by(CandidateRanking.rank_position).all()
        
        if not rankings:
            raise HTTPException(status_code=404, detail="No rankings found for this job")
        
        return {
            'job_id': job_id,
            'total_rankings': len(rankings),
            'rankings': [
                {
                    'candidate_id': r.candidate_id,
                    'candidate_name': r.candidate.name,
                    'rank_position': r.rank_position,
                    'overall_rank_score': r.overall_rank_score,
                    'skill_match_score': r.skill_match_score,
                    'experience_match_score': r.experience_match_score,
                    'seniority_alignment_score': r.seniority_alignment_score,
                    'percentile': r.percentile
                }
                for r in rankings
            ]
        }
    
    except Exception as e:
        logger.error(f"Error fetching rankings: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ranking-details/{ranking_id}")
async def get_ranking_details(ranking_id: str, db: Session = Depends(get_db)):
    """Get detailed ranking information with full explanation"""
    try:
        ranking = db.query(CandidateRanking).filter(
            CandidateRanking.id == ranking_id
        ).first()
        
        if not ranking:
            raise HTTPException(status_code=404, detail="Ranking not found")
        
        return {
            'ranking_id': ranking.id,
            'candidate_id': ranking.candidate_id,
            'candidate_name': ranking.candidate.name,
            'job_id': ranking.job_id,
            'job_title': ranking.job.title,
            'rank_position': ranking.rank_position,
            'overall_rank_score': ranking.overall_rank_score,
            'scores': {
                'skill_match': ranking.skill_match_score,
                'experience_match': ranking.experience_match_score,
                'seniority_alignment': ranking.seniority_alignment_score
            },
            'matched_skills_count': ranking.matched_skills_count,
            'missing_skills_count': ranking.missing_skills_count,
            'explanation': ranking.explanation,
            'bias_mitigated': ranking.bias_mitigated,
            'created_at': ranking.created_at
        }
    
    except Exception as e:
        logger.error(f"Error fetching ranking details: {e}")
        raise HTTPException(status_code=500, detail=str(e))
