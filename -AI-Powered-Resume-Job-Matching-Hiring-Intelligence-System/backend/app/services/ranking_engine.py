"""
Ranking Model Service
Ranks candidates against job descriptions using ML models
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
import pickle
import os

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency fallback
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class RankingModel:
    """ML-based candidate ranking model"""
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize ranking model"""
        if SentenceTransformer is not None:
            try:
                self.sbert = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as exc:
                logger.warning(f"SBERT unavailable in ranking model; using heuristic ranking only: {exc}")
                self.sbert = None
        else:
            logger.warning("sentence-transformers not installed; using heuristic ranking only")
            self.sbert = None
        self.model = None
        self.model_path = model_path
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            logger.warning(f"Model not found at {model_path}, using heuristic ranking")
    
    def load_model(self, path: str):
        """Load pre-trained ranking model"""
        try:
            with open(path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"Loaded ranking model from {path}")
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            self.model = None
    
    def save_model(self, path: str):
        """Save ranking model"""
        try:
            with open(path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Saved ranking model to {path}")
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
    
    def compute_skill_match_score(self, candidate_skills: List[Dict], 
                                  required_skills: List[Dict],
                                  preferred_skills: List[Dict]) -> Tuple[float, List[str], List[str]]:
        """
        Compute skill match score between candidate and job
        
        Returns:
            (score: 0-100, matched_skills: list, missing_skills: list)
        """
        candidate_skill_names = {s.get('skill', '').lower() for s in candidate_skills}
        
        matched = []
        missing_required = []
        missing_preferred = []
        
        # Check required skills
        for req_skill in required_skills:
            skill_name = req_skill.get('skill', '').lower()
            skill_normalized = skill_name.strip().replace(' ', '').replace('_', '')
            
            found = False
            for cand_skill in candidate_skill_names:
                cand_normalized = cand_skill.replace(' ', '').replace('_', '')
                
                # Exact or substring match
                if skill_normalized in cand_normalized or cand_normalized in skill_normalized:
                    matched.append(skill_name)
                    found = True
                    break
            
            if not found:
                missing_required.append(skill_name)
        
        # Check preferred skills
        for pref_skill in preferred_skills:
            skill_name = pref_skill.get('skill', '').lower()
            skill_normalized = skill_name.strip().replace(' ', '').replace('_', '')
            
            found = False
            for cand_skill in candidate_skill_names:
                cand_normalized = cand_skill.replace(' ', '').replace('_', '')
                
                if skill_normalized in cand_normalized or cand_normalized in skill_normalized:
                    matched.append(skill_name)
                    found = True
                    break
            
            if not found:
                missing_preferred.append(skill_name)
        
        # Calculate score
        total_required = len(required_skills)
        total_preferred = len(preferred_skills)
        total_skills = total_required + total_preferred
        
        if total_skills == 0:
            return 50.0, matched, missing_required + missing_preferred
        
        # Weighted score: required skills weight more heavily
        required_matched = len([s for s in matched if s in [r.get('skill', '').lower() for r in required_skills]])
        
        if total_required > 0:
            required_score = (required_matched / total_required) * 100
        else:
            required_score = 50
        
        preferred_matched = len([s for s in matched if s in [p.get('skill', '').lower() for p in preferred_skills]])
        
        if total_preferred > 0:
            preferred_score = (preferred_matched / total_preferred) * 100
        else:
            preferred_score = 50
        
        # Weighted average (70% required, 30% preferred)
        if total_required > 0 and total_preferred > 0:
            score = (required_score * 0.7) + (preferred_score * 0.3)
        elif total_required > 0:
            score = required_score
        else:
            score = preferred_score
        
        return min(score, 100.0), matched, missing_required + missing_preferred
    
    def compute_experience_match_score(self, candidate_years: float,
                                      required_years: Optional[float]) -> float:
        """
        Compute experience match score
        
        Score logic:
        - Perfect match: 100
        - Exceeds by < 2 years: 95-100
        - Exceeds by > 2 years: 90-95
        - Within 1 year below: 85-90
        - 1-2 years below: 70-85
        - More than 2 years below: 40-70
        """
        if required_years is None or required_years == 0:
            return 70.0  # Neutral score if no requirement
        
        diff = candidate_years - required_years
        
        if diff >= -0.5 and diff <= 1:
            return 100.0
        elif diff > 1 and diff <= 2:
            return 95.0
        elif diff > 2:
            return 90.0
        elif diff >= -1:
            return 85.0
        elif diff >= -2:
            return 70.0
        else:
            # Heavily penalize if significantly below
            return max(40.0, 70.0 - (abs(diff) * 10))
    
    def compute_seniority_alignment_score(self, candidate_seniority: str,
                                         job_level: Optional[str]) -> float:
        """
        Compute seniority alignment score
        
        Logic: Penalize misalignment but allow over-qualification
        """
        if job_level is None:
            return 70.0  # Neutral
        
        seniority_levels = ['intern', 'junior', 'mid_level', 'senior', 'lead']
        
        try:
            candidate_idx = seniority_levels.index(candidate_seniority.lower().replace('-', '_'))
        except ValueError:
            candidate_idx = 2  # Default to mid level
        
        try:
            job_idx = seniority_levels.index(job_level.lower().replace('-', '_'))
        except ValueError:
            job_idx = 2  # Default to mid level
        
        diff = candidate_idx - job_idx
        
        if diff == 0:
            return 100.0
        elif diff == 1:
            return 90.0  # Slightly over-qualified
        elif diff >= 2:
            return 80.0  # Over-qualified
        elif diff == -1:
            return 75.0  # Slightly under-qualified (risky)
        else:
            return max(50.0, 75.0 + (diff * 10))  # Increasingly worse as gap widens
    
    def compute_ranking_scores(self, candidate: Dict, job: Dict) -> Dict:
        """Compute all ranking scores for a candidate-job pair"""
        
        candidate_skills = candidate.get('skills', [])
        candidate_years = candidate.get('years_of_experience', 0)
        candidate_seniority = candidate.get('inferred_seniority', 'junior')
        
        job_required_skills = job.get('required_skills', [])
        job_preferred_skills = job.get('preferred_skills', [])
        job_required_years = job.get('years_of_experience_required', None)
        job_level = job.get('job_level', None)
        
        # Component scores
        skill_score, matched_skills, missing_skills = self.compute_skill_match_score(
            candidate_skills,
            job_required_skills,
            job_preferred_skills
        )
        
        experience_score = self.compute_experience_match_score(
            candidate_years,
            job_required_years
        )
        
        seniority_score = self.compute_seniority_alignment_score(
            candidate_seniority,
            job_level
        )
        
        # Weights (configurable)
        SKILL_WEIGHT = 0.45
        EXPERIENCE_WEIGHT = 0.35
        SENIORITY_WEIGHT = 0.20
        
        overall_score = (
            skill_score * SKILL_WEIGHT +
            experience_score * EXPERIENCE_WEIGHT +
            seniority_score * SENIORITY_WEIGHT
        )
        
        return {
            'overall_rank_score': overall_score,
            'skill_match_score': skill_score,
            'experience_match_score': experience_score,
            'seniority_alignment_score': seniority_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'matched_skills_count': len(matched_skills),
            'missing_skills_count': len(missing_skills),
            'years_of_exp_match': candidate_years
        }
    
    def rank_candidates(self, candidates: List[Dict], job: Dict) -> List[Dict]:
        """Rank multiple candidates against a job"""
        
        rankings = []
        
        for candidate in candidates:
            scores = self.compute_ranking_scores(candidate, job)
            rankings.append({
                'candidate_id': candidate.get('id'),
                'candidate_name': candidate.get('name'),
                'candidate_seniority': candidate.get('inferred_seniority'),
                **scores
            })
        
        # Sort by overall score (descending)
        rankings.sort(key=lambda x: x['overall_rank_score'], reverse=True)
        
        # Add rank position and percentile
        for idx, ranking in enumerate(rankings):
            ranking['rank_position'] = idx + 1
            ranking['percentile'] = ((len(rankings) - idx) / len(rankings)) * 100
        
        return rankings


def create_ranking_objects_for_db(rankings: List[Dict], job_id: str) -> List[Dict]:
    """Convert ranking results to database objects"""
    db_objects = []
    
    for ranking in rankings:
        db_objects.append({
            'job_id': job_id,
            'candidate_id': ranking['candidate_id'],
            'overall_rank_score': ranking['overall_rank_score'],
            'skill_match_score': ranking['skill_match_score'],
            'experience_match_score': ranking['experience_match_score'],
            'seniority_alignment_score': ranking['seniority_alignment_score'],
            'rank_position': ranking['rank_position'],
            'percentile': ranking['percentile'],
            'matched_skills_count': ranking['matched_skills_count'],
            'missing_skills_count': ranking['missing_skills_count'],
            'years_of_exp_match': ranking['years_of_exp_match']
        })
    
    return db_objects
