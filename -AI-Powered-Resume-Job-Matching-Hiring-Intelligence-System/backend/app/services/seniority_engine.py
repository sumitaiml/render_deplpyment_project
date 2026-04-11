"""
Seniority Inference Service
Infers candidate seniority level based on experience, skills, and role progression
"""

import logging
from typing import Dict, List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class SeniorityLevel(str, Enum):
    """Seniority levels"""
    INTERN = "intern"
    JUNIOR = "junior"
    MID_LEVEL = "mid_level"
    SENIOR = "senior"
    LEAD = "lead"


class SeniorityInference:
    """Infers candidate seniority using multiple signals"""
    
    # Keywords indicating role level advancement
    JUNIOR_KEYWORDS = ['junior', 'intern', 'entry', 'associate', 'graduate']
    MID_KEYWORDS = ['mid', 'senior', 'specialist', 'expert', 'lead technical']
    SENIOR_KEYWORDS = ['senior', 'principal', 'architect', 'tech lead', 'manager']
    LEAD_KEYWORDS = ['director', 'head', 'vp', 'cto', 'ceo', 'founder', 'lead engineer']
    
    # Skills indicating technical depth
    ADVANCED_TECH_SKILLS = [
        'system design', 'architecture', 'microservices', 'distributed systems',
        'machine learning', 'deep learning', 'kubernetes', 'terraform',
        'ddd', 'cqrs', 'event sourcing'
    ]
    
    # Keywords for leadership experience
    LEADERSHIP_KEYWORDS = ['led', 'managed', 'team', 'mentor', 'direction', 'strategy']
    
    def __init__(self):
        """Initialize seniority inference engine"""
        pass
    
    def infer_from_years_of_experience(self, years: float) -> Tuple[SeniorityLevel, float]:
        """
        Infer seniority primarily from years of experience
        Returns (seniority_level, confidence_0_to_1)
        """
        if years < 1:
            return SeniorityLevel.INTERN, 0.9
        elif years < 2:
            return SeniorityLevel.JUNIOR, 0.85
        elif years < 5:
            return SeniorityLevel.MID_LEVEL, 0.75
        elif years < 10:
            return SeniorityLevel.SENIOR, 0.8
        else:
            return SeniorityLevel.LEAD, 0.8
    
    def analyze_role_progression(self, experiences: List[Dict]) -> Dict:
        """Analyze role progression over time"""
        analysis = {
            'role_advancement': False,
            'roles_held': [],
            'companies': [],
            'avg_tenure_per_role': 0.0,
            'indicators': []
        }
        
        if not experiences:
            return analysis
        
        for exp in experiences:
            role = exp.get('role', '').lower()
            company = exp.get('company', '')
            duration = exp.get('duration_years', 0)
            
            analysis['roles_held'].append(role)
            if company not in analysis['companies']:
                analysis['companies'].append(company)
        
        # Calculate average tenure
        total_duration = sum(e.get('duration_years', 0) for e in experiences)
        if len(experiences) > 0:
            analysis['avg_tenure_per_role'] = total_duration / len(experiences)
        
        # Check for advancement
        if len(experiences) > 1:
            first_role = experiences[0].get('role', '').lower()
            last_role = experiences[-1].get('role', '').lower()
            
            first_level = self._classify_role_level(first_role)
            last_level = self._classify_role_level(last_role)
            
            if last_level > first_level:
                analysis['role_advancement'] = True
                analysis['indicators'].append("Clear role progression observed")
        
        # Leadership indicators
        leadership_keywords = ['lead', 'manager', 'head', 'director', 'architect']
        for role in analysis['roles_held']:
            if any(kw in role for kw in leadership_keywords):
                analysis['indicators'].append("Leadership experience detected")
                break
        
        return analysis
    
    def _classify_role_level(self, role: str) -> int:
        """Classify role seniority numerically (0-5)"""
        role = role.lower()
        
        for keyword in self.LEAD_KEYWORDS:
            if keyword in role:
                return 4
        
        for keyword in self.SENIOR_KEYWORDS:
            if keyword in role:
                return 3
        
        for keyword in self.MID_KEYWORDS:
            if keyword in role:
                return 2
        
        for keyword in self.JUNIOR_KEYWORDS:
            if keyword in role:
                return 1
        
        return 1  # Default to junior if unclear
    
    def analyze_skill_depth(self, skills: List[Dict]) -> Dict:
        """Analyze technical skill depth"""
        analysis = {
            'total_skills': len(skills),
            'explicit_skills': sum(1 for s in skills if s.get('is_explicit', False)),
            'implicit_skills': sum(1 for s in skills if not s.get('is_explicit', False)),
            'advanced_skills': 0,
            'skill_diversity': 'low',  # low, medium, high
            'proficiency_average': 0.0,
            'indicators': []
        }
        
        if not skills:
            return analysis
        
        # Count advanced skills
        advanced_count = 0
        for skill in skills:
            skill_name = skill.get('skill', '').lower()
            for adv_skill in self.ADVANCED_TECH_SKILLS:
                if adv_skill in skill_name:
                    advanced_count += 1
                    break
        
        analysis['advanced_skills'] = advanced_count
        
        # Skill diversity (categories)
        skill_categories = set()
        category_keywords = {
            'backend': ['java', 'python', 'node', 'spring', 'django', 'flask'],
            'frontend': ['react', 'angular', 'vue', 'javascript', 'html', 'css'],
            'database': ['sql', 'mongodb', 'postgres', 'mysql', 'redis'],
            'cloud': ['aws', 'azure', 'gcp', 'docker', 'kubernetes'],
            'devops': ['docker', 'kubernetes', 'jenkins', 'terraform', 'ci/cd'],
            'data': ['machine learning', 'tensorflow', 'pytorch', 'pandas', 'spark'],
        }
        
        for skill in skills:
            skill_name = skill.get('skill', '').lower()
            for category, keywords in category_keywords.items():
                if any(kw in skill_name for kw in keywords):
                    skill_categories.add(category)
        
        if len(skill_categories) >= 4:
            analysis['skill_diversity'] = 'high'
            analysis['indicators'].append("High skill diversity (full-stack capability)")
        elif len(skill_categories) >= 2:
            analysis['skill_diversity'] = 'medium'
            analysis['indicators'].append("Medium skill diversity")
        else:
            analysis['skill_diversity'] = 'low'
        
        # Calculate proficiency average
        proficiency_scores = {
            'beginner': 0.2,
            'intermediate': 0.5,
            'advanced': 0.8,
            'expert': 1.0
        }
        
        total_proficiency = 0
        for skill in skills:
            level = skill.get('proficiency_level', 'intermediate')
            total_proficiency += proficiency_scores.get(level, 0.5)
        
        if skills:
            analysis['proficiency_average'] = total_proficiency / len(skills)
        
        if advanced_count > 0:
            analysis['indicators'].append(f"{advanced_count} advanced/architectural skills")
        
        return analysis
    
    def infer_seniority(self, resume_data: Dict) -> Dict:
        """
        Main method to infer seniority from all available signals
        
        Args:
            resume_data: Dictionary with years_of_experience, experience, skills, etc.
        
        Returns:
            Dictionary with inferred_seniority, confidence, and reasoning
        """
        years_of_exp = resume_data.get('years_of_experience', 0)
        experience_entries = resume_data.get('experience', [])
        skills = resume_data.get('skills', [])
        
        scores = {}
        reasoning = []
        
        # Signal 1: Years of experience (40% weight)
        exp_seniority, exp_confidence = self.infer_from_years_of_experience(years_of_exp)
        scores['experience'] = {
            'seniority': exp_seniority,
            'confidence': exp_confidence,
            'years': years_of_exp
        }
        reasoning.append(f"Years of experience: {years_of_exp} years → {exp_seniority.value} ({exp_confidence:.0%})")
        
        # Signal 2: Role progression (30% weight)
        role_analysis = self.analyze_role_progression(experience_entries)
        if role_analysis['role_advancement']:
            role_boost = 1  # One level up
            scores['role_progression'] = {
                'advancement_score': 1.0,
                'senior_boost': role_boost
            }
            reasoning.append("Career progression detected (role advancement)")
        else:
            scores['role_progression'] = {
                'advancement_score': 0.5,
                'senior_boost': 0
            }
        
        # Leadership experience
        if any(ind in role_analysis.get('indicators', []) for ind in ["Leadership experience detected"]):
            scores['leadership'] = 1.0
            reasoning.append("Leadership/management experience detected")
        
        # Signal 3: Skill depth and diversity (30% weight)
        skill_analysis = self.analyze_skill_depth(skills)
        scores['skills'] = skill_analysis
        reasoning.extend(skill_analysis['indicators'])
        
        # Aggregate signals to determine final seniority
        final_seniority = self._aggregate_signals(
            exp_seniority,
            role_analysis,
            skill_analysis,
            years_of_exp
        )
        
        # Calculate confidence (average of signals)
        confidence = (
            exp_confidence * 0.4 +
            (0.8 if role_analysis['role_advancement'] else 0.5) * 0.3 +
            (skill_analysis['proficiency_average']) * 0.3
        )
        
        return {
            'predicted_seniority': final_seniority,
            'confidence_score': min(confidence, 1.0),
            'confidence_reasons': reasoning,
            'experience_analysis': {
                'years_of_experience': years_of_exp,
                'number_of_roles': len(experience_entries),
                'avg_tenure_per_role': role_analysis['avg_tenure_per_role'],
                'detected_advancement': role_analysis['role_advancement']
            },
            'skill_analysis': {
                'total_skills': skill_analysis['total_skills'],
                'advanced_skills': skill_analysis['advanced_skills'],
                'skill_diversity': skill_analysis['skill_diversity'],
                'average_proficiency': skill_analysis['proficiency_average']
            },
            'detailed_signals': scores
        }
    
    def _aggregate_signals(self, experience_level: SeniorityLevel, 
                          role_analysis: Dict, skill_analysis: Dict, 
                          years: float) -> SeniorityLevel:
        """Aggregate multiple signals to determine final seniority"""
        
        # Start with experience-based level
        level_score = self._level_to_score(experience_level)
        
        # Boost based on role advancement
        if role_analysis['role_advancement']:
            level_score += 0.5
        
        # Boost based on skill depth
        if skill_analysis['advanced_skills'] > 3 and skill_analysis['skill_diversity'] == 'high':
            level_score += 0.5
        elif skill_analysis['skill_diversity'] == 'high':
            level_score += 0.3
        elif skill_analysis['skill_diversity'] == 'medium':
            level_score += 0.1
        
        # Boost for high proficiency
        if skill_analysis['proficiency_average'] > 0.75:
            level_score += 0.3
        
        # Convert back to level
        level_score = min(level_score, 4)  # Max to LEAD
        return self._score_to_level(level_score)
    
    def _level_to_score(self, level: SeniorityLevel) -> float:
        """Convert seniority level to numeric score"""
        mapping = {
            SeniorityLevel.INTERN: 0.0,
            SeniorityLevel.JUNIOR: 1.0,
            SeniorityLevel.MID_LEVEL: 2.0,
            SeniorityLevel.SENIOR: 3.0,
            SeniorityLevel.LEAD: 4.0
        }
        return mapping.get(level, 1.0)
    
    def _score_to_level(self, score: float) -> SeniorityLevel:
        """Convert numeric score to seniority level"""
        if score < 0.5:
            return SeniorityLevel.INTERN
        elif score < 1.5:
            return SeniorityLevel.JUNIOR
        elif score < 2.5:
            return SeniorityLevel.MID_LEVEL
        elif score < 3.5:
            return SeniorityLevel.SENIOR
        else:
            return SeniorityLevel.LEAD
