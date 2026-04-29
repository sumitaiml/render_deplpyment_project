"""
Ranking Model Service
Ranks candidates against job descriptions using ML models
"""

import logging
import re
import os
import numpy as np
from typing import Dict, List, Tuple, Optional
import pickle
import os

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency fallback
    SentenceTransformer = None

logger = logging.getLogger(__name__)
RENDER_LIGHTWEIGHT_MODE = os.getenv("RENDER") == "true" or os.getenv("LIGHTWEIGHT_RUNTIME") == "true"


class RankingModel:
    """ML-based candidate ranking model"""

    SEMANTIC_MATCH_THRESHOLD = 0.62
    DEFAULT_SKILL_EVIDENCE_WEIGHT = 1.0
    SKILL_SOURCE_WEIGHTS = {
        'experience': 1.0,
        'work experience': 1.0,
        'project': 0.92,
        'projects': 0.92,
        'resume': 0.82,
        'skills_section': 0.76,
        'skill section': 0.76,
        'inferred': 0.68,
        'skill_graph_inference': 0.65,
        'education': 0.7,
    }
    
    def __init__(self, model_path: Optional[str] = None):
        """Initialize ranking model"""
        if RENDER_LIGHTWEIGHT_MODE:
            self.sbert = None
            logger.info("Render lightweight mode enabled; skipping SBERT load in RankingModel")
        elif SentenceTransformer is not None:
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

        self._embedding_cache: Dict[str, np.ndarray] = {}

    def _normalize_skill_text(self, text: str) -> str:
        """Normalize skill text for exact and semantic comparison."""
        return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()

    def _skills_exact_match(self, candidate_skill: str, job_skill: str) -> bool:
        """Check whether two skill strings match exactly or by substring."""
        candidate_norm = self._normalize_skill_text(candidate_skill)
        job_norm = self._normalize_skill_text(job_skill)

        if not candidate_norm or not job_norm:
            return False

        return candidate_norm == job_norm or candidate_norm in job_norm or job_norm in candidate_norm

    def _get_text_embedding(self, text: str) -> Optional[np.ndarray]:
        """Get a cached embedding for semantic comparison."""
        if self.sbert is None:
            return None

        normalized_text = self._normalize_skill_text(text)
        if not normalized_text:
            return None

        if normalized_text in self._embedding_cache:
            return self._embedding_cache[normalized_text]

        try:
            embedding = self.sbert.encode([normalized_text], normalize_embeddings=True)
            vector = np.asarray(embedding[0], dtype=float)
            self._embedding_cache[normalized_text] = vector
            return vector
        except Exception as exc:
            logger.warning(f"Unable to compute semantic embedding for '{text}': {exc}")
            return None

    def _semantic_similarity(self, candidate_skill: str, job_skill: str) -> float:
        """Compute semantic similarity between two skill strings."""
        candidate_embedding = self._get_text_embedding(candidate_skill)
        job_embedding = self._get_text_embedding(job_skill)

        if candidate_embedding is None or job_embedding is None:
            return 0.0

        similarity = float(np.dot(candidate_embedding, job_embedding))
        return max(0.0, min(similarity, 1.0))

    def _skill_evidence_weight(self, candidate_skill: Dict) -> float:
        """Estimate how strong the evidence is for a candidate skill."""
        source = str(candidate_skill.get('mentioned_in') or candidate_skill.get('source') or '').strip().lower()
        if not source and 'confidence_score' not in candidate_skill and 'is_explicit' not in candidate_skill:
            return self.DEFAULT_SKILL_EVIDENCE_WEIGHT

        weight = self.SKILL_SOURCE_WEIGHTS.get(source, self.DEFAULT_SKILL_EVIDENCE_WEIGHT)

        if candidate_skill.get('is_explicit') is False:
            weight *= 0.92

        confidence = candidate_skill.get('confidence_score')
        if confidence is not None:
            try:
                confidence_value = max(0.0, min(float(confidence), 1.0))
                weight *= 0.9 + (confidence_value * 0.1)
            except (TypeError, ValueError):
                pass

        return max(0.45, min(weight, 1.0))

    def _normalize_skill_name(self, skill_name: str) -> str:
        """Normalize a skill name for stable comparison and display."""
        return self._normalize_skill_text(skill_name)

    def _select_best_candidate_match(self, candidate_skills: List[Dict], job_skill_name: str) -> Dict:
        """Select the best matching candidate skill for a requested job skill."""
        best_match = {
            'found': False,
            'candidate_skill_name': None,
            'match_confidence': 0.0,
            'evidence_weight': 0.0,
            'combined_score': 0.0,
            'candidate_skill': None,
        }

        if not job_skill_name:
            return best_match

        for candidate_skill in candidate_skills:
            candidate_skill_name = str(candidate_skill.get('skill') or '').strip()
            if not candidate_skill_name:
                continue

            matched = False
            match_confidence = 0.0

            if self._skills_exact_match(candidate_skill_name, job_skill_name):
                matched = True
                match_confidence = 1.0
            elif self.sbert is not None:
                similarity = self._semantic_similarity(candidate_skill_name, job_skill_name)
                if similarity >= self.SEMANTIC_MATCH_THRESHOLD:
                    matched = True
                    match_confidence = similarity

            if not matched:
                continue

            evidence_weight = self._skill_evidence_weight(candidate_skill)
            combined_score = match_confidence * evidence_weight

            if combined_score > best_match['combined_score']:
                best_match = {
                    'found': True,
                    'candidate_skill_name': candidate_skill_name,
                    'match_confidence': match_confidence,
                    'evidence_weight': evidence_weight,
                    'combined_score': combined_score,
                    'candidate_skill': candidate_skill,
                }

        return best_match

    def _build_skill_match_breakdown(
        self,
        candidate_skills: List[Dict],
        required_skills: List[Dict],
        preferred_skills: List[Dict],
        candidate_resume_text: Optional[str] = None,
        weight_config: Optional[Dict] = None,
    ) -> Dict:
        """Compute evidence-aware skill scoring while preserving backward-compatible outputs."""
        candidate_skill_records = [s for s in candidate_skills if isinstance(s, dict) and s.get('skill')]

        matched_skills: List[str] = []
        missing_skills: List[str] = []
        required_skill_matches: List[Dict] = []
        preferred_skill_matches: List[Dict] = []
        evidence_map: Dict[str, List[str]] = {}

        required_score_total = 0.0
        required_weight_total = 0.0
        preferred_score_total = 0.0
        preferred_weight_total = 0.0
        evidence_weights: List[float] = []

        normalized_weight_config = weight_config or {}
        required_skill_bias = max(0.0, min(float(normalized_weight_config.get('required_skill_weight', 0.85)), 1.0))
        preferred_skill_bias = max(0.0, min(float(normalized_weight_config.get('preferred_skill_weight', 0.15)), 1.0))
        evidence_weight_factor = max(0.0, min(float(normalized_weight_config.get('evidence_weight', 1.0)), 1.0))

        total_skill_bias = required_skill_bias + preferred_skill_bias
        if total_skill_bias <= 0:
            required_skill_share = 0.85
            preferred_skill_share = 0.15
        else:
            required_skill_share = required_skill_bias / total_skill_bias
            preferred_skill_share = preferred_skill_bias / total_skill_bias

        def evaluate_skill(req_skill: Dict, is_required: bool) -> Dict:
            skill_name = str(req_skill.get('skill', '')).strip()
            importance = req_skill.get('importance_score', req_skill.get('importance', 1.0))
            try:
                importance_value = max(0.0, float(importance))
            except (TypeError, ValueError):
                importance_value = 1.0

            match = self._select_best_candidate_match(candidate_skill_records, skill_name)
            normalized_skill_name = self._normalize_skill_name(skill_name)
            evidence_snippets: List[str] = []

            if match['found'] and match['candidate_skill_name']:
                matched_skills.append(normalized_skill_name)
                adjusted_evidence_weight = (1.0 - evidence_weight_factor) + (match['evidence_weight'] * evidence_weight_factor)
                evidence_weights.append(adjusted_evidence_weight)

                if candidate_resume_text:
                    evidence_snippets = self._find_evidence_snippets(match['candidate_skill_name'], candidate_resume_text)
                    if not evidence_snippets and match['candidate_skill_name'] != skill_name:
                        evidence_snippets = self._find_evidence_snippets(skill_name, candidate_resume_text)
                    if evidence_snippets:
                        evidence_map[normalized_skill_name] = evidence_snippets
            else:
                missing_skills.append(normalized_skill_name)

            skill_result = {
                'skill': normalized_skill_name,
                'matched': match['found'],
                'match_confidence': match['match_confidence'],
                'evidence_weight': match['evidence_weight'] if match['found'] else 0.0,
                'combined_score': match['combined_score'] if match['found'] else 0.0,
                'evidence': evidence_snippets,
                'importance': importance_value,
            }

            if is_required:
                required_skill_matches.append(skill_result)
                required_score_total_nonlocal[0] += skill_result['combined_score'] * importance_value
                required_weight_total_nonlocal[0] += importance_value
            else:
                preferred_skill_matches.append(skill_result)
                preferred_score_total_nonlocal[0] += skill_result['combined_score'] * importance_value
                preferred_weight_total_nonlocal[0] += importance_value

            return skill_result

        required_score_total_nonlocal = [0.0]
        required_weight_total_nonlocal = [0.0]
        preferred_score_total_nonlocal = [0.0]
        preferred_weight_total_nonlocal = [0.0]

        for req_skill in required_skills:
            evaluate_skill(req_skill, True)

        for pref_skill in preferred_skills:
            evaluate_skill(pref_skill, False)

        matched_skills = list(dict.fromkeys(matched_skills))
        missing_skills = list(dict.fromkeys(missing_skills))

        required_coverage = required_score_total_nonlocal[0] / required_weight_total_nonlocal[0] if required_weight_total_nonlocal[0] > 0 else None
        preferred_coverage = preferred_score_total_nonlocal[0] / preferred_weight_total_nonlocal[0] if preferred_weight_total_nonlocal[0] > 0 else None

        if required_coverage is not None and preferred_coverage is not None:
            base_score = (required_coverage * 100.0 * required_skill_share) + (preferred_coverage * 100.0 * preferred_skill_share)
        elif required_coverage is not None:
            base_score = required_coverage * 100.0
        elif preferred_coverage is not None:
            base_score = preferred_coverage * 100.0
        else:
            base_score = 50.0

        critical_penalty = (1.0 - required_coverage) * 20.0 if required_coverage is not None else 0.0
        final_score = max(0.0, min(100.0, base_score - critical_penalty))

        evidence_confidence = sum(evidence_weights) / len(evidence_weights) if evidence_weights else self.DEFAULT_SKILL_EVIDENCE_WEIGHT

        return {
            'skill_match_score': final_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'matched_required_skills': [item['skill'] for item in required_skill_matches if item['matched']],
            'missing_required_skills': [item['skill'] for item in required_skill_matches if not item['matched']],
            'matched_preferred_skills': [item['skill'] for item in preferred_skill_matches if item['matched']],
            'missing_preferred_skills': [item['skill'] for item in preferred_skill_matches if not item['matched']],
            'required_coverage': None if required_coverage is None else max(0.0, min(required_coverage * 100.0, 100.0)),
            'preferred_coverage': None if preferred_coverage is None else max(0.0, min(preferred_coverage * 100.0, 100.0)),
            'skill_evidence_score': max(0.0, min(evidence_confidence * 100.0, 100.0)),
            'skill_evidence': evidence_map,
            'matched_skills_count': len(matched_skills),
            'missing_skills_count': len(missing_skills),
            'critical_missing_skills': [item['skill'] for item in required_skill_matches if not item['matched']],
        }
    
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
                                  preferred_skills: List[Dict],
                                  candidate_resume_text: Optional[str] = None,
                                  return_evidence: bool = False,
                                  weight_config: Optional[Dict] = None) -> Tuple[float, List[str], List[str]]:
        """
        Compute skill match score between candidate and job
        
        Returns:
            (score: 0-100, matched_skills: list, missing_skills: list)
        """
        breakdown = self._build_skill_match_breakdown(
            candidate_skills,
            required_skills,
            preferred_skills,
            candidate_resume_text=candidate_resume_text,
            weight_config=weight_config,
        )

        if return_evidence:
            return (
                breakdown['skill_match_score'],
                breakdown['matched_skills'],
                breakdown['missing_skills'],
                breakdown['skill_evidence'],
            )

        return breakdown['skill_match_score'], breakdown['matched_skills'], breakdown['missing_skills']

    def _find_evidence_snippets(self, skill_name: str, resume_text: str, max_snippets: int = 3) -> List[str]:
        """Find short text snippets in the resume that evidence a given skill."""
        if not skill_name or not resume_text:
            return []

        skill_tokens = [t.lower() for t in re.split(r"\s+", skill_name) if t]

        # split resume into lines and sentences
        candidates = []
        for line in resume_text.splitlines():
            l = line.strip()
            if not l:
                continue
            lower_line = l.lower()
            # prefer lines that contain all tokens
            if all(tok in lower_line for tok in skill_tokens):
                candidates.append(l)

        # fallback: include lines that contain any token
        if len(candidates) < max_snippets:
            for line in resume_text.splitlines():
                l = line.strip()
                if not l:
                    continue
                lower_line = l.lower()
                if any(tok in lower_line for tok in skill_tokens) and l not in candidates:
                    candidates.append(l)
                if len(candidates) >= max_snippets:
                    break

        # truncate and return
        return candidates[:max_snippets]
    
    def compute_experience_match_score(self, candidate_years: float,
                                      required_years: Optional[float],
                                      strictness: float = 1.0) -> float:
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
        strictness = max(0.5, min(float(strictness), 2.0))
        
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
            return max(40.0, 70.0 - (abs(diff) * 10 * strictness))
    
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
    
    def compute_ranking_scores(self, candidate: Dict, job: Dict, weight_config: Optional[Dict] = None) -> Dict:
        """Compute all ranking scores for a candidate-job pair"""
        
        candidate_skills = candidate.get('skills', [])
        candidate_years = candidate.get('years_of_experience', 0)
        candidate_seniority = candidate.get('inferred_seniority', 'junior')
        
        job_required_skills = job.get('required_skills', [])
        job_preferred_skills = job.get('preferred_skills', [])
        job_required_years = job.get('years_of_experience_required', None)
        job_level = job.get('job_level', None)
        
        breakdown = self._build_skill_match_breakdown(
            candidate_skills,
            job_required_skills,
            job_preferred_skills,
            candidate_resume_text=candidate.get('resume_text', ''),
            weight_config=weight_config,
        )

        skill_score = breakdown['skill_match_score']
        matched_skills = breakdown['matched_skills']
        missing_skills = breakdown['missing_skills']
        skill_evidence = breakdown['skill_evidence']
        
        experience_score = self.compute_experience_match_score(
            candidate_years,
            job_required_years,
            strictness=max(0.5, min(float((weight_config or {}).get('experience_strictness', 1.0)), 2.0)),
        )
        
        seniority_score = self.compute_seniority_alignment_score(
            candidate_seniority,
            job_level
        )
        
        normalized_weight_config = weight_config or {}
        skill_weight = max(0.0, float(normalized_weight_config.get('skill_weight', 0.45)))
        experience_weight = max(0.0, float(normalized_weight_config.get('experience_weight', 0.35)))
        seniority_weight = max(0.0, float(normalized_weight_config.get('seniority_weight', 0.20)))

        total_weight = skill_weight + experience_weight + seniority_weight
        if total_weight <= 0:
            skill_weight, experience_weight, seniority_weight = 0.45, 0.35, 0.20
            total_weight = 1.0

        skill_weight /= total_weight
        experience_weight /= total_weight
        seniority_weight /= total_weight
        
        overall_score = (
            skill_score * skill_weight +
            experience_score * experience_weight +
            seniority_score * seniority_weight
        )
        
        return {
            'overall_rank_score': overall_score,
            'skill_match_score': skill_score,
            'skill_evidence': skill_evidence,
            'must_have_coverage': breakdown['required_coverage'],
            'nice_to_have_coverage': breakdown['preferred_coverage'],
            'skill_evidence_score': breakdown['skill_evidence_score'],
            'critical_missing_skills': breakdown['critical_missing_skills'],
            'experience_match_score': experience_score,
            'seniority_alignment_score': seniority_score,
            'matched_skills': matched_skills,
            'missing_skills': missing_skills,
            'matched_skills_count': len(matched_skills),
            'missing_skills_count': len(missing_skills),
            'years_of_exp_match': candidate_years
        }
    
    def rank_candidates(self, candidates: List[Dict], job: Dict, weight_config: Optional[Dict] = None) -> List[Dict]:
        """Rank multiple candidates against a job"""
        
        rankings = []
        
        for candidate in candidates:
            scores = self.compute_ranking_scores(candidate, job, weight_config=weight_config)
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
