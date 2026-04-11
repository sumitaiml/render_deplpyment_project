"""
Comprehensive Backend Tests
Tests for resume parsing, skill extraction, seniority inference, and ranking
"""

import pytest
import json
from datetime import datetime
from app.services import (
    ResumeParser,
    SkillExtractor,
    SkillGraph,
    SeniorityInference,
    RankingModel,
)
from app.services.explainability_engine import ExplainabilityEngine


class TestResumeParser:
    """Test resume parsing functionality"""
    
    def setup_method(self):
        """Setup for each test"""
        self.parser = ResumeParser()
    
    def test_extract_name(self):
        """Test name extraction"""
        text = "John Doe\njohn.doe@example.com\n123-456-7890"
        name = self.parser.extract_name(text)
        assert name is not None
        assert "John" in name or "john" in name.lower()
    
    def test_extract_email(self):
        """Test email extraction"""
        text = "John Doe (john.doe@example.com) Senior Engineer"
        email = self.parser.extract_email(text)
        assert email == "john.doe@example.com"
    
    def test_extract_phone(self):
        """Test phone extraction"""
        text = "Contact: 123-456-7890"
        phone = self.parser.extract_phone(text)
        assert phone is not None
    
    def test_extract_years_of_experience(self):
        """Test years of experience extraction"""
        experience = [
            {'company': 'TechCorp', 'role': 'Engineer', 'duration_years': 3},
            {'company': 'StartupInc', 'role': 'Senior Engineer', 'duration_years': 2}
        ]
        years = self.parser.extract_years_of_experience("", experience)
        assert years == 5.0
    
    def test_extract_skills_from_context(self):
        """Test skill extraction from context"""
        context = "Experienced with Python, Java, React, and PostgreSQL"
        skills = self.parser._extract_skills_from_context(context)
        assert len(skills) > 0
        assert any('python' in s.lower() for s in skills)


class TestSkillExtractor:
    """Test skill extraction and graph inference"""
    
    def setup_method(self):
        """Setup for each test"""
        self.skill_graph = SkillGraph()
        self.extractor = SkillExtractor(self.skill_graph)
    
    def test_normalize_skill_name(self):
        """Test skill name normalization"""
        assert self.skill_graph.normalize_skill_name("python") == "Python"
        assert self.skill_graph.normalize_skill_name("JAVA") == "Java"
    
    def test_get_related_skills(self):
        """Test skill graph traversal"""
        related = self.skill_graph.get_related_skills("Java", depth=1)
        assert len(related) > 0
        assert any('backend' in s.lower() for s in related)
    
    def test_extract_explicit_skills(self):
        """Test explicit skill extraction"""
        text = """SKILLS
        Python, Java, JavaScript, React, PostgreSQL
        Docker, Kubernetes, AWS"""
        
        skills = self.extractor.extract_explicit_skills(text)
        assert len(skills) > 0
    
    def test_extract_implicit_skills(self):
        """Test implicit skill inference"""
        text = """Built REST APIs using Spring Boot. Designed microservices architecture. 
        Deployed applications using Docker and Kubernetes."""
        
        skills = self.extractor.extract_implicit_skills(text)
        assert len(skills) > 0


class TestSeniorityInference:
    """Test seniority level inference"""
    
    def setup_method(self):
        """Setup for each test"""
        self.seniority_engine = SeniorityInference()
    
    def test_infer_from_years_junior(self):
        """Test junior seniority inference"""
        level, confidence = self.seniority_engine.infer_from_years_of_experience(1.5)
        assert level.value == "junior"
        assert confidence > 0.7
    
    def test_infer_from_years_senior(self):
        """Test senior seniority inference"""
        level, confidence = self.seniority_engine.infer_from_years_of_experience(7.0)
        assert level.value == "senior"
        assert confidence > 0.7
    
    def test_infer_from_years_lead(self):
        """Test lead seniority inference"""
        level, confidence = self.seniority_engine.infer_from_years_of_experience(12.0)
        assert level.value == "lead"
        assert confidence > 0.7
    
    def test_role_progression_analysis(self):
        """Test role progression detection"""
        experiences = [
            {'role': 'Junior Developer', 'duration_years': 2},
            {'role': 'Senior Developer', 'duration_years': 3},
            {'role': 'Tech Lead', 'duration_years': 2}
        ]
        
        analysis = self.seniority_engine.analyze_role_progression(experiences)
        assert analysis['role_advancement'] == True
        assert len(analysis['roles_held']) == 3
    
    def test_skill_depth_analysis(self):
        """Test skill depth analysis"""
        skills = [
            {'skill': 'Python', 'proficiency_level': 'expert'},
            {'skill': 'React', 'proficiency_level': 'advanced'},
            {'skill': 'PostgreSQL', 'proficiency_level': 'advanced'},
            {'skill': 'Docker', 'proficiency_level': 'intermediate'},
            {'skill': 'Kubernetes', 'proficiency_level': 'intermediate'}
        ]
        
        analysis = self.seniority_engine.analyze_skill_depth(skills)
        assert analysis['total_skills'] == 5
        assert analysis['proficiency_average'] > 0.5
    
    def test_full_seniority_inference(self):
        """Test complete seniority inference"""
        resume_data = {
            'years_of_experience': 5.0,
            'experience': [
                {'role': 'Junior Developer', 'duration_years': 2},
                {'role': 'Senior Developer', 'duration_years': 3}
            ],
            'skills': [
                {'skill': 'Python', 'proficiency_level': 'expert', 'is_explicit': True},
                {'skill': 'React', 'proficiency_level': 'advanced', 'is_explicit': True},
                {'skill': 'System Design', 'proficiency_level': 'advanced', 'is_explicit': False}
            ]
        }
        
        result = self.seniority_engine.infer_seniority(resume_data)
        assert 'predicted_seniority' in result
        assert 'confidence_score' in result
        assert result['confidence_score'] > 0.5
        assert result['confidence_score'] <= 1.0


class TestRankingModel:
    """Test candidate ranking model"""
    
    def setup_method(self):
        """Setup for each test"""
        self.ranker = RankingModel()
    
    def test_compute_skill_match_score(self):
        """Test skill matching"""
        candidate_skills = [
            {'skill': 'Python', 'proficiency_level': 'expert'},
            {'skill': 'React', 'proficiency_level': 'advanced'},
            {'skill': 'PostgreSQL', 'proficiency_level': 'intermediate'}
        ]
        
        required_skills = [
            {'skill': 'Python', 'importance': 1.0},
            {'skill': 'PostgreSQL', 'importance': 1.0}
        ]
        
        preferred_skills = [
            {'skill': 'React', 'importance': 0.5}
        ]
        
        score, matched, missing = self.ranker.compute_skill_match_score(
            candidate_skills,
            required_skills,
            preferred_skills
        )
        
        assert score > 0
        assert len(matched) >= 2
        assert score <= 100
    
    def test_compute_experience_match_score(self):
        """Test experience matching"""
        # Perfect match
        score = self.ranker.compute_experience_match_score(5.0, 5.0)
        assert score == 100.0
        
        # Above requirement
        score = self.ranker.compute_experience_match_score(7.0, 5.0)
        assert score >= 90.0
        
        # Below requirement
        score = self.ranker.compute_experience_match_score(3.0, 5.0)
        assert 0 < score < 100
    
    def test_compute_seniority_alignment_score(self):
        """Test seniority alignment"""
        # Perfect match
        score = self.ranker.compute_seniority_alignment_score('senior', 'senior')
        assert score == 100.0
        
        # Over-qualified
        score = self.ranker.compute_seniority_alignment_score('lead', 'senior')
        assert score >= 80.0
        
        # Under-qualified
        score = self.ranker.compute_seniority_alignment_score('junior', 'senior')
        assert 0 < score < 100
    
    def test_full_ranking(self):
        """Test complete candidate ranking"""
        candidates = [
            {
                'id': 'cand1',
                'name': 'Alice',
                'years_of_experience': 5.0,
                'inferred_seniority': 'mid_level',
                'skills': [
                    {'skill': 'Python', 'proficiency_level': 'expert'},
                    {'skill': 'React', 'proficiency_level': 'advanced'}
                ]
            },
            {
                'id': 'cand2',
                'name': 'Bob',
                'years_of_experience': 3.0,
                'inferred_seniority': 'junior',
                'skills': [
                    {'skill': 'Python', 'proficiency_level': 'intermediate'},
                    {'skill': 'PostgreSQL', 'proficiency_level': 'intermediate'}
                ]
            }
        ]
        
        job = {
            'title': 'Senior Python Developer',
            'job_level': 'senior',
            'years_of_experience_required': 5.0,
            'required_skills': [
                {'skill': 'Python', 'importance': 1.0}
            ],
            'preferred_skills': [
                {'skill': 'React', 'importance': 0.5}
            ]
        }
        
        rankings = self.ranker.rank_candidates(candidates, job)
        
        assert len(rankings) == 2
        assert rankings[0]['rank_position'] == 1
        assert rankings[1]['rank_position'] == 2
        assert rankings[0]['overall_rank_score'] >= rankings[1]['overall_rank_score']


class TestExplainabilityEngine:
    """Test explainability generation"""
    
    def setup_method(self):
        """Setup for each test"""
        self.explainability = ExplainabilityEngine()
    
    def test_generate_skill_explanation(self):
        """Test skill explanation generation"""
        explanation = self.explainability._generate_skill_explanation(
            matched_skills=['Python', 'React', 'PostgreSQL'],
            missing_skills=['Kubernetes', 'Terraform'],
            skill_score=75.0
        )
        
        assert 'details' in explanation
        assert 'strengths' in explanation
        assert 'gaps' in explanation
        assert len(explanation['details']) > 0
    
    def test_generate_experience_explanation(self):
        """Test experience explanation"""
        explanation = self.explainability._generate_experience_explanation(
            candidate_years=5.0,
            required_years=5.0,
            exp_score=100.0
        )
        
        assert 'analysis' in explanation
        assert explanation['strength'] is not None
    
    def test_generate_seniority_explanation(self):
        """Test seniority explanation"""
        explanation = self.explainability._generate_seniority_explanation(
            candidate_seniority='senior',
            job_level='senior',
            seniority_score=100.0
        )
        
        assert 'reasoning' in explanation
        assert explanation['strength'] is not None
    
    def test_generate_ranking_explanation(self):
        """Test full ranking explanation generation"""
        candidate = {
            'name': 'Alice Smith',
            'years_of_experience': 5.0,
            'inferred_seniority': 'mid_level'
        }
        
        job = {
            'title': 'Senior Engineer'
        }
        
        ranking = {
            'rank_position': 2,
            'overall_rank_score': 78.0,
            'skill_match_score': 85.0,
            'experience_match_score': 90.0,
            'seniority_alignment_score': 75.0,
            'matched_skills': ['Python', 'React'],
            'missing_skills': ['Kubernetes']
        }
        
        explanation = self.explainability.generate_ranking_explanation(
            candidate, job, ranking
        )
        
        assert 'reason' in explanation
        assert 'overall_summary' in explanation
        assert explanation['overall_summary'] is not None


@pytest.fixture
def sample_resume():
    """Fixture for sample resume data"""
    return {
        'name': 'John Doe',
        'email': 'john@example.com',
        'phone': '123-456-7890',
        'years_of_experience': 5.0,
        'experience': [
            {
                'company': 'TechCorp',
                'role': 'Senior Engineer',
                'duration_years': 3,
                'description': 'Led team of 5 engineers',
                'skills_used': ['Python', 'React', 'AWS']
            }
        ],
        'education': [
            {
                'institution': 'MIT',
                'degree': 'B.S.',
                'field_of_study': 'Computer Science'
            }
        ],
        'projects': [
            {
                'name': 'ML Pipeline',
                'description': 'Built production ML pipeline',
                'technologies': ['TensorFlow', 'Python']
            }
        ]
    }


def test_end_to_end_pipeline(sample_resume):
    """Test complete candidate ranking pipeline"""
    
    # Step 1: Parse resume (simulated)
    parsed_resume = sample_resume
    
    # Step 2: Extract skills
    skill_extractor = SkillExtractor()
    skills_result = skill_extractor.extract_all_skills(parsed_resume)
    assert len(skills_result['all_skills']) > 0
    
    # Step 3: Infer seniority
    seniority_engine = SeniorityInference()
    seniority_result = seniority_engine.infer_seniority(parsed_resume)
    assert seniority_result['confidence_score'] > 0
    
    # Step 4: Rank against job
    ranker = RankingModel()
    job = {
        'title': 'Senior Python Developer',
        'job_level': 'senior',
        'years_of_experience_required': 5.0,
        'required_skills': [{'skill': 'Python', 'importance': 1.0}],
        'preferred_skills': [{'skill': 'React', 'importance': 0.5}]
    }
    
    candidate_data = {
        'id': 'cand1',
        'name': parsed_resume['name'],
        'years_of_experience': parsed_resume['years_of_experience'],
        'inferred_seniority': seniority_result['predicted_seniority'].value,
        'skills': skills_result['all_skills']
    }
    
    rankings = ranker.rank_candidates([candidate_data], job)
    
    # Step 5: Generate explanation
    explainer = ExplainabilityEngine()
    explanation = explainer.generate_ranking_explanation(
        candidate_data,
        job,
        rankings[0]
    )
    
    assert 'overall_summary' in explanation
    print("✅ Full pipeline test passed!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
