"""
Skill Extraction & Skill Graph Service
Extracts skills, normalizes them, and infers related skills using skill graph
"""

import re
import json
import logging
from typing import List, Dict, Tuple, Optional, Set
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency fallback
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class SkillGraph:
    """Manages skill relationships and inference"""
    
    def __init__(self, ontology_path: Optional[str] = None):
        """Initialize skill graph"""
        self.skills = {}
        self.relationships = {}
        if SentenceTransformer is not None:
            try:
                self.sbert = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as exc:
                logger.warning(f"SBERT unavailable in SkillGraph; continuing without embeddings: {exc}")
                self.sbert = None
        else:
            logger.warning("sentence-transformers not installed; SkillGraph embeddings disabled")
            self.sbert = None
        
        if ontology_path:
            self.load_ontology(ontology_path)
        else:
            self._init_default_ontology()
    
    def _init_default_ontology(self):
        """Initialize with default skill ontology"""
        # Base skills with categories
        base_skills = {
            # Programming Languages
            "Python": {"category": "Programming Language", "level": 1},
            "Java": {"category": "Programming Language", "level": 1},
            "JavaScript": {"category": "Programming Language", "level": 1},
            "TypeScript": {"category": "Programming Language", "level": 1},
            "C++": {"category": "Programming Language", "level": 1},
            "Go": {"category": "Programming Language", "level": 1},
            "Rust": {"category": "Programming Language", "level": 1},
            
            # Web Frameworks
            "React": {"category": "Web Framework", "level": 2},
            "Angular": {"category": "Web Framework", "level": 2},
            "Vue.js": {"category": "Web Framework", "level": 2},
            "Node.js": {"category": "Web Framework", "level": 2},
            "Django": {"category": "Web Framework", "level": 2},
            "Flask": {"category": "Web Framework", "level": 2},
            "Spring Boot": {"category": "Web Framework", "level": 2},
            "Express.js": {"category": "Web Framework", "level": 2},
            
            # Databases
            "SQL": {"category": "Database", "level": 2},
            "PostgreSQL": {"category": "Database", "level": 2},
            "MySQL": {"category": "Database", "level": 2},
            "MongoDB": {"category": "Database", "level": 2},
            "Redis": {"category": "Database", "level": 2},
            "Elasticsearch": {"category": "Database", "level": 2},
            
            # Cloud Platforms
            "AWS": {"category": "Cloud", "level": 2},
            "Azure": {"category": "Cloud", "level": 2},
            "GCP": {"category": "Cloud", "level": 2},
            "Docker": {"category": "Cloud", "level": 2},
            "Kubernetes": {"category": "Cloud", "level": 2},
            
            # Data Science
            "Machine Learning": {"category": "Data Science", "level": 2},
            "Deep Learning": {"category": "Data Science", "level": 2},
            "TensorFlow": {"category": "Data Science", "level": 2},
            "PyTorch": {"category": "Data Science", "level": 2},
            "Scikit-learn": {"category": "Data Science", "level": 2},
            "Pandas": {"category": "Data Science", "level": 2},
            "NumPy": {"category": "Data Science", "level": 2},
            
            # Domains
            "Backend Development": {"category": "Domain", "level": 1},
            "Frontend Development": {"category": "Domain", "level": 1},
            "Full Stack Development": {"category": "Domain", "level": 1},
            "DevOps": {"category": "Domain", "level": 1},
            "Data Engineering": {"category": "Domain", "level": 1},
            
            # APIs & Architecture
            "REST API": {"category": "Architecture", "level": 2},
            "GraphQL": {"category": "Architecture", "level": 2},
            "Microservices": {"category": "Architecture", "level": 2},
        }
        
        self.skills = base_skills
        
        # Define relationships
        self.relationships = {
            # Programming skills
            ("Spring Boot", "Java"): {"type": "requires", "strength": 0.95},
            ("Java", "Backend Development"): {"type": "implies", "strength": 0.8},
            ("Python", "Backend Development"): {"type": "implies", "strength": 0.8},
            ("React", "JavaScript"): {"type": "requires", "strength": 0.9},
            ("Angular", "TypeScript"): {"type": "requires", "strength": 0.85},
            ("Vue.js", "JavaScript"): {"type": "requires", "strength": 0.9},
            
            # Database relationships
            ("PostgreSQL", "SQL"): {"type": "implies", "strength": 0.9},
            ("MySQL", "SQL"): {"type": "implies", "strength": 0.9},
            ("MongoDB", "NoSQL"): {"type": "implies", "strength": 0.8},
            
            # Cloud relationships
            ("Docker", "DevOps"): {"type": "implies", "strength": 0.8},
            ("Kubernetes", "DevOps"): {"type": "implies", "strength": 0.85},
            ("Kubernetes", "Docker"): {"type": "related_to", "strength": 0.8},
            
            # Domain mapping
            ("React", "Frontend Development"): {"type": "implies", "strength": 0.9},
            ("Angular", "Frontend Development"): {"type": "implies", "strength": 0.9},
            ("Node.js", "Backend Development"): {"type": "implies", "strength": 0.85},
            ("Spring Boot", "Backend Development"): {"type": "implies", "strength": 0.9},
        }
    
    def load_ontology(self, path: str):
        """Load skill ontology from file"""
        try:
            with open(path, 'r') as f:
                data = json.load(f)
                self.skills = data.get('skills', {})
                self.relationships = {tuple(k.split('->'))if isinstance(k, str) else k: v 
                                    for k, v in data.get('relationships', {}).items()}
        except Exception as e:
            logger.warning(f"Failed to load ontology: {e}. Using default.")
            self._init_default_ontology()
    
    def save_ontology(self, path: str):
        """Save skill ontology to file"""
        data = {
            'skills': self.skills,
            'relationships': {f"{k[0]}->{k[1]}": v for k, v in self.relationships.items()}
        }
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def normalize_skill_name(self, skill: str) -> str:
        """Normalize skill name to match ontology"""
        skill = skill.strip()
        
        # Direct match
        for known_skill in self.skills.keys():
            if skill.lower() == known_skill.lower():
                return known_skill
        
        # Partial match
        for known_skill in self.skills.keys():
            if skill.lower() in known_skill.lower() or known_skill.lower() in skill.lower():
                return known_skill
        
        # Return original if no match
        return skill
    
    def get_related_skills(self, skill_name: str, depth: int = 1) -> Set[str]:
        """Get skills related to a given skill using the graph"""
        related = set()
        visited = set()
        
        def traverse(skill, current_depth):
            if current_depth > depth or skill in visited:
                return
            
            visited.add(skill)
            
            # Find all relationships where this skill is source or target
            for (src, tgt), rel in self.relationships.items():
                if src == skill and current_depth < depth:
                    related.add(tgt)
                    traverse(tgt, current_depth + 1)
                elif tgt == skill and current_depth < depth:
                    related.add(src)
                    traverse(src, current_depth + 1)
        
        traverse(skill_name, 0)
        return related
    
    def infer_skills_from_context(self, context: str) -> List[Dict]:
        """Infer skills from text context using NLP"""
        inferred_skills = []
        
        # Explicit skill patterns
        patterns = {
            "API development": ["REST API", "GraphQL"],
            "microservices": ["Microservices", "Docker", "Kubernetes"],
            "database design": ["SQL", "Database Design"],
            "full stack": ["Full Stack Development"],
            "DevOps": ["DevOps", "Docker", "Kubernetes", "CI/CD"],
        }
        
        context_lower = context.lower()
        
        for pattern, skills in patterns.items():
            if pattern in context_lower:
                for skill in skills:
                    inferred_skills.append({
                        'skill': skill,
                        'confidence': 0.7,
                        'type': 'inferred',
                        'pattern': pattern
                    })
        
        return inferred_skills


class SkillExtractor:
    """Extracts skills from resume text"""
    
    def __init__(self, skill_graph: Optional[SkillGraph] = None):
        """Initialize skill extractor"""
        self.skill_graph = skill_graph or SkillGraph()
        if SentenceTransformer is not None:
            try:
                self.sbert = SentenceTransformer("all-MiniLM-L6-v2")
            except Exception as exc:
                logger.warning(f"SBERT unavailable in SkillExtractor; using rule-based extraction: {exc}")
                self.sbert = None
        else:
            self.sbert = None
    
    def extract_explicit_skills(self, text: str) -> List[Dict]:
        """Extract explicitly mentioned skills from text"""
        explicit_skills = []
        
        # Look for "Skills" section
        sections = re.split(
            r'(?:SKILLS?|TECHNICAL SKILLS?|CORE COMPETENCIES?|EXPERTISE)',
            text,
            flags=re.IGNORECASE
        )
        
        if len(sections) > 1:
            skills_text = sections[1].split('\n')[0:20]  # Take first 20 lines
            
            # Split by common delimiters
            skills_str = " ".join(skills_text)
            skills = re.split(r'[,;•·\n]', skills_str)
            
            for skill in skills:
                skill = skill.strip()
                if len(skill) > 2 and len(skill) < 50:
                    normalized = self.skill_graph.normalize_skill_name(skill)
                    explicit_skills.append({
                        'skill': normalized,
                        'confidence': 0.9,
                        'is_explicit': True,
                        'mentioned_in': 'skills_section'
                    })
        
        return explicit_skills
    
    def extract_implicit_skills(self, text: str) -> List[Dict]:
        """Extract implicit skills from work descriptions and projects"""
        implicit_skills = []
        
        # Pattern-based extraction
        patterns = {
            "Built (?:REST )?(?:APIs?|services?)": ["REST API", "Backend Development"],
            "Developed (?:web )?(?:applications?|apps?)": ["Full Stack Development"],
            "Led (?:team|project)": ["Leadership", "Project Management"],
            "Designed (?:database|schema|architecture)": ["Database Design", "System Design"],
            "Optimized (?:performance|queries|database)": ["Performance Optimization"],
            "Deployed (?:application|service)": ["DevOps", "CI/CD"],
            "Containerized.*(?:Docker|container)": ["Docker", "DevOps"],
            "Orchestrated.*(?:Kubernetes|K8s)": ["Kubernetes", "DevOps"],
        }
        
        for pattern, skills in patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                for skill in skills:
                    implicit_skills.append({
                        'skill': skill,
                        'confidence': 0.7,
                        'is_explicit': False,
                        'mentioned_in': 'inferred',
                        'pattern': pattern
                    })
        
        return implicit_skills
    
    def extract_all_skills(self, resume_data: Dict) -> Dict:
        """Extract all skills (explicit and implicit) from parsed resume"""
        resume_text = resume_data.get('resume_text', '')
        experience = resume_data.get('experience', [])
        education = resume_data.get('education', [])
        projects = resume_data.get('projects', [])
        
        # Combine all text
        combined_text = f"{resume_text}\n"
        combined_text += "\n".join([
            f"{e.get('description', '')} {' '.join(e.get('skills_used', []))}"
            for e in experience
        ])
        combined_text += "\n".join([
            f"{' '.join(p.get('technologies', []))}"
            for p in projects
        ])
        
        # Extract explicit and implicit
        explicit = self.extract_explicit_skills(combined_text)
        implicit = self.extract_implicit_skills(combined_text)
        
        # Normalize and deduplicate
        all_skills = {}
        for skill_dict in explicit + implicit:
            skill_name = skill_dict['skill']
            if skill_name not in all_skills or skill_dict['confidence'] > all_skills[skill_name]['confidence']:
                all_skills[skill_name] = skill_dict
        
        # Infer related skills
        inferred_related = []
        for skill_name in all_skills.keys():
            related = self.skill_graph.get_related_skills(skill_name, depth=1)
            for related_skill in related:
                if related_skill not in all_skills:
                    inferred_related.append({
                        'skill': related_skill,
                        'confidence': 0.6,
                        'is_explicit': False,
                        'mentioned_in': 'skill_graph_inference',
                        'inferred_from': skill_name
                    })
        
        return {
            'explicit_skills': list(all_skills.values()),
            'inferred_skills': inferred_related,
            'all_skills': list(all_skills.values()) + inferred_related,
            'skill_count': len(all_skills) + len(inferred_related),
            'primary_skills': sorted(all_skills.values(), key=lambda x: x['confidence'], reverse=True)[:5]
        }


def extract_skills_for_candidate(resume_data: Dict) -> List[Dict]:
    """Helper function to extract skills for a candidate"""
    extractor = SkillExtractor()
    result = extractor.extract_all_skills(resume_data)
    return result['all_skills']
