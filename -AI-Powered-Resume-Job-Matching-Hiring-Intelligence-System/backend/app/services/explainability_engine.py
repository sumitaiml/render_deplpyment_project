"""
Explainability Engine
Generates human-readable explanations for ranking decisions and candidate evaluations
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ExplainabilityEngine:
    """Generates explainable AI outputs for ranking and evaluation"""
    
    def __init__(self):
        """Initialize explainability engine"""
        pass
    
    def generate_ranking_explanation(self, candidate: Dict, job: Dict, ranking: Dict) -> Dict:
        """
        Generate comprehensive explanation for why a candidate was ranked at a certain position
        
        Returns: {
            reason: str,
            matched_skills: list,
            missing_skills: list,
            skill_match_details: list,
            experience_analysis: str,
            seniority_reasoning: str,
            overall_summary: str,
            highlighted_strengths: list,
            areas_for_growth: list
        }
        """
        
        explanation = {
            'reason': '',
            'matched_skills': ranking.get('matched_skills', []),
            'missing_skills': ranking.get('missing_skills', []),
            'skill_match_details': [],
            'experience_analysis': '',
            'seniority_reasoning': '',
            'overall_summary': '',
            'highlighted_strengths': [],
            'areas_for_growth': []
        }
        
        # Main ranking reason
        overall_score = ranking['overall_rank_score']
        rank_position = ranking.get('rank_position', 0)
        
        if overall_score >= 85:
            explanation['reason'] = f"Excellent candidate (#{rank_position}) with strong alignment across skills, experience, and seniority."
        elif overall_score >= 70:
            explanation['reason'] = f"Good candidate (#{rank_position}) with solid match on key requirements. Some gaps to address."
        elif overall_score >= 50:
            explanation['reason'] = f"Moderate candidate (#{rank_position}). Has potential but lacks some key qualifications."
        else:
            explanation['reason'] = f"Candidate ranked #{rank_position}. Significant gaps in required skills or experience."
        
        # Skill analysis
        skill_explanation = self._generate_skill_explanation(
            ranking.get('matched_skills', []),
            ranking.get('missing_skills', []),
            ranking['skill_match_score']
        )
        explanation['skill_match_details'] = skill_explanation['details']
        explanation['highlighted_strengths'].extend(skill_explanation['strengths'])
        explanation['areas_for_growth'].extend(skill_explanation['gaps'])
        
        # Experience analysis
        experience_explanation = self._generate_experience_explanation(
            candidate.get('years_of_experience', 0),
            job.get('years_of_experience_required'),
            ranking['experience_match_score']
        )
        explanation['experience_analysis'] = experience_explanation['analysis']
        if experience_explanation['strength']:
            explanation['highlighted_strengths'].append(experience_explanation['strength'])
        if experience_explanation['gap']:
            explanation['areas_for_growth'].append(experience_explanation['gap'])
        
        # Seniority alignment
        seniority_explanation = self._generate_seniority_explanation(
            candidate.get('inferred_seniority', 'junior'),
            job.get('job_level'),
            ranking['seniority_alignment_score']
        )
        explanation['seniority_reasoning'] = seniority_explanation['reasoning']
        if seniority_explanation['strength']:
            explanation['highlighted_strengths'].append(seniority_explanation['strength'])
        
        # Overall summary
        explanation['overall_summary'] = self._generate_overall_summary(
            explanation,
            ranking,
            candidate,
            job
        )
        
        return explanation
    
    def _generate_skill_explanation(self, matched_skills: List[str], 
                                   missing_skills: List[str],
                                   skill_score: float) -> Dict:
        """Generate skill-specific explanation"""
        details = []
        strengths = []
        gaps = []
        
        if matched_skills:
            matched_str = ', '.join(matched_skills[:5])
            if len(matched_skills) > 5:
                matched_str += f", and {len(matched_skills) - 5} more"
            
            details.append({
                'category': 'Matched Skills',
                'items': matched_skills,
                'summary': f"Matched {len(matched_skills)} required/preferred skills: {matched_str}"
            })
            
            strength_msg = f"Strong technical foundation with {len(matched_skills)} relevant skills"
            strengths.append(strength_msg)
        
        if missing_skills:
            missing_str = ', '.join(missing_skills[:3])
            if len(missing_skills) > 3:
                missing_str += f" and {len(missing_skills) - 3} others"
            
            details.append({
                'category': 'Missing Skills',
                'items': missing_skills,
                'summary': f"Missing {len(missing_skills)} skills: {missing_str}"
            })
            
            gap_msg = f"Could develop {len(missing_skills)} additional skills mentioned in job posting"
            gaps.append(gap_msg)
        
        # Skill score interpretation
        if skill_score >= 80:
            strengths.append("Excellent skill match (80%+ coverage)")
        elif skill_score >= 60:
            strengths.append("Good skill match (60%+ coverage)")
        elif skill_score >= 40:
            gaps.append("Moderate skill coverage (40%+) - would benefit from upskilling")
        
        return {
            'details': details,
            'strengths': strengths,
            'gaps': gaps
        }
    
    def _generate_experience_explanation(self, candidate_years: float,
                                        required_years: Optional[float],
                                        exp_score: float) -> Dict:
        """Generate experience-specific explanation"""
        result = {
            'analysis': '',
            'strength': None,
            'gap': None
        }
        
        if required_years is None:
            result['analysis'] = f"Candidate has {candidate_years:.1f} years of experience (no specific requirement for this role)."
            return result
        
        diff = candidate_years - required_years
        
        if diff >= 0:
            result['analysis'] = f"Candidate has {candidate_years:.1f} years of experience, meeting the requirement of {required_years} years."
            if diff > 2:
                result['strength'] = f"Significantly exceeds experience requirement by {diff:.1f} years"
            else:
                result['strength'] = f"Meets experience requirement with {diff:.1f} additional years"
        else:
            result['analysis'] = f"Candidate has {candidate_years:.1f} years of experience, which is {abs(diff):.1f} years below the requirement of {required_years} years."
            result['gap'] = f"Lacks {abs(diff):.1f} years of required experience"
        
        return result
    
    def _generate_seniority_explanation(self, candidate_seniority: str,
                                       job_level: Optional[str],
                                       seniority_score: float) -> Dict:
        """Generate seniority alignment explanation"""
        result = {
            'reasoning': '',
            'strength': None,
            'gap': None
        }
        
        if job_level is None:
            result['reasoning'] = f"Candidate inferred as {candidate_seniority.replace('_', ' ').title()}."
            return result
        
        result['reasoning'] = f"Candidate seniority ({candidate_seniority.replace('_', ' ').title()}) vs. Job level ({job_level.replace('_', ' ').title()}). "
        
        seniority_order = ['intern', 'junior', 'mid_level', 'senior', 'lead']
        
        try:
            candidate_idx = seniority_order.index(candidate_seniority.lower())
            job_idx = seniority_order.index(job_level.lower())
            diff = candidate_idx - job_idx
            
            if diff == 0:
                result['reasoning'] += "Perfect seniority alignment."
                result['strength'] = f"Exact seniority match for the {job_level} position"
            elif diff > 0:
                result['reasoning'] += f"Candidate is {diff} level(s) more senior (over-qualified)."
                result['strength'] = f"Over-qualified candidate brings depth and mentoring potential"
            else:
                result['reasoning'] += f"Candidate is {abs(diff)} level(s) less senior."
                result['gap'] = f"Candidate may require more mentorship/support to hit the ground running"
        
        except ValueError:
            result['reasoning'] += "Unable to precisely match seniority levels."
        
        return result
    
    def _generate_overall_summary(self, explanation: Dict, ranking: Dict,
                                 candidate: Dict, job: Dict) -> str:
        """Generate overall summary statement"""
        
        overall_score = ranking['overall_rank_score']
        rank_pos = ranking.get('rank_position', '?')
        candidate_name = candidate.get('name', 'Candidate')
        job_title = job.get('title', 'Position')
        
        # Build summary based on scores and strengths/gaps
        summary_parts = []
        
        summary_parts.append(f"{candidate_name} is ranked #{rank_pos} for the {job_title} position with an overall match score of {overall_score:.0f}/100.")
        
        # Highlight top strengths
        if explanation['highlighted_strengths']:
            top_strengths = explanation['highlighted_strengths'][:2]
            summary_parts.append(f"Key strengths: {', '.join(top_strengths)}.")
        
        # Highlight gaps
        if explanation['areas_for_growth']:
            top_gaps = explanation['areas_for_growth'][:2]
            summary_parts.append(f"Areas for growth: {', '.join(top_gaps)}.")
        
        # Hiring recommendation
        if overall_score >= 80:
            summary_parts.append("RECOMMENDATION: Highly recommended for interview - strong overall fit.")
        elif overall_score >= 65:
            summary_parts.append("RECOMMENDATION: Consider for interview - reasonable match with some areas to address.")
        elif overall_score >= 50:
            summary_parts.append("RECOMMENDATION: May interview if pipeline is thin - address specific gaps before proceeding.")
        else:
            summary_parts.append("RECOMMENDATION: Not recommended at this stage - significant gaps in key qualifications.")
        
        return " ".join(summary_parts)
    
    def generate_bias_mitigation_report(self, original_rankings: List[Dict],
                                       mitigated_rankings: List[Dict]) -> Dict:
        """Generate report on how bias mitigation affected rankings"""
        
        report = {
            'bias_mitigation_applied': True,
            'attributes_masked': ['name', 'gender indicators', 'age proxies'],
            'ranking_stability': 0.0,
            'candidates_reranked': 0,
            'details': []
        }
        
        if not original_rankings or not mitigated_rankings:
            return report
        
        # Compare positions
        original_positions = {r['candidate_id']: r.get('rank_position', 0) for r in original_rankings}
        mitigated_positions = {r['candidate_id']: r.get('rank_position', 0) for r in mitigated_rankings}
        
        position_changes = 0
        total = len(original_positions)
        
        for cand_id in original_positions:
            if original_positions.get(cand_id) != mitigated_positions.get(cand_id):
                position_changes += 1
                
                orig_pos = original_positions[cand_id]
                new_pos = mitigated_positions[cand_id]
                
                if new_pos < orig_pos:
                    report['details'].append({
                        'candidate_id': cand_id,
                        'original_position': orig_pos,
                        'mitigated_position': new_pos,
                        'change': 'improved'
                    })
                else:
                    report['details'].append({
                        'candidate_id': cand_id,
                        'original_position': orig_pos,
                        'mitigated_position': new_pos,
                        'change': 'adjusted'
                    })
        
        report['candidates_reranked'] = position_changes
        report['ranking_stability'] = (total - position_changes) / total if total > 0 else 1.0
        
        return report
