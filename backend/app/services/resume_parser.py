"""
Resume Parser Service
Extracts structured information from resumes in various formats
"""

import re
import base64
import io
import os
import PyPDF2
from docx import Document
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import spacy
import logging

try:
    from sentence_transformers import SentenceTransformer
except Exception:  # pragma: no cover - optional dependency fallback
    SentenceTransformer = None

logger = logging.getLogger(__name__)
RENDER_LIGHTWEIGHT_MODE = os.getenv("RENDER") == "true" or os.getenv("LIGHTWEIGHT_RUNTIME") == "true"


class ResumeParser:
    """Main resume parser class"""
    
    def __init__(self):
        """Initialize parser with NLP models"""
        if RENDER_LIGHTWEIGHT_MODE:
            self.nlp = None
            self.sbert = None
            logger.info("Render lightweight mode enabled; skipping spaCy/SBERT load in ResumeParser")
        else:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except Exception as exc:
                logger.warning("spaCy model not found. Install with: python -m spacy download en_core_web_sm")
                self.nlp = None

            if SentenceTransformer is not None:
                try:
                    self.sbert = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception as exc:
                    logger.warning(f"SBERT unavailable, using rule-based parsing only: {exc}")
                    self.sbert = None
            else:
                logger.warning("sentence-transformers not installed; using rule-based parsing only")
                self.sbert = None
        self.experience_keywords = [
            "worked", "responsible for", "led", "managed", "developed", "designed",
            "implemented", "maintained", "supported", "coordinated", "supervised",
            "contributed", "collaborated", "created", "built", "engineered"
        ]
        
        self.education_keywords = [
            "bachelor", "master", "phd", "b.s.", "b.a.", "m.s.", "m.tech", "b.tech",
            "diploma", "certificate", "associate degree", "degree", "graduated"
        ]
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """Extract text from PDF file"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF: {e}")
            return ""
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Extract text from DOCX file"""
        try:
            doc = Document(io.BytesIO(file_content))
            text = ""
            for para in doc.paragraphs:
                text += para.text + "\n"
            return text
        except Exception as e:
            logger.error(f"Error extracting DOCX: {e}")
            return ""
    
    def convert_file_to_text(self, file_content, file_format: str) -> str:
        """Convert various file formats to text"""
        try:
            # Handle both bytes and string inputs
            if isinstance(file_content, str):
                # If it's a string, try base64 decode for PDF/DOCX, else treat as text
                if file_format.lower() == "pdf":
                    try:
                        binary_data = base64.b64decode(file_content)
                        return self.extract_text_from_pdf(binary_data)
                    except:
                        logger.warning("Failed to base64 decode PDF, trying as raw")
                        return file_content
                elif file_format.lower() == "docx":
                    try:
                        binary_data = base64.b64decode(file_content)
                        return self.extract_text_from_docx(binary_data)
                    except:
                        logger.warning("Failed to base64 decode DOCX, trying as raw")
                        return file_content
                elif file_format.lower() == "txt":
                    try:
                        return base64.b64decode(file_content).decode('utf-8')
                    except:
                        return file_content
                else:
                    return file_content
            
            elif isinstance(file_content, bytes):
                # If it's bytes, convert directly based on format
                if file_format.lower() == "pdf":
                    return self.extract_text_from_pdf(file_content)
                elif file_format.lower() == "docx":
                    return self.extract_text_from_docx(file_content)
                elif file_format.lower() == "txt":
                    return file_content.decode('utf-8', errors='ignore')
                else:
                    return file_content.decode('utf-8', errors='ignore')
            
            else:
                return str(file_content)
                
        except Exception as e:
            logger.error(f"Error converting file to text: {e}")
            return str(file_content)
    
    def extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name from resume"""
        # Usually appears in first few lines
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if len(line) > 2 and len(line) < 100 and not any(char.isdigit() for char in line):
                # Filter out common junk
                if not any(keyword in line.lower() for keyword in 
                          ["email", "phone", "address", "linkedin", "github", "skills"]):
                    return line
        return None
    
    def extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        match = re.search(email_pattern, text)
        return match.group(0) if match else None
    
    def extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        phone_patterns = [
            r'\+?1?\s*\(?[0-9]{3}\)?[\s.-]?[0-9]{3}[\s.-]?[0-9]{4}',  # US
            r'\+[0-9]{1,3}\s?[0-9]{6,14}',  # International
            r'[0-9]{10}',  # 10 digits
        ]
        for pattern in phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def extract_years_of_experience(self, text: str, experience_entries: List[Dict]) -> float:
        """Calculate total years of experience from resume"""
        total_years = 0.0
        
        for entry in experience_entries:
            if 'duration_years' in entry and entry['duration_years']:
                total_years += entry['duration_years']
        
        # Fallback: look for explicit year mentions
        if total_years == 0:
            year_pattern = r'(\d+)\s*(?:years?|yrs?)\s*(?:of\s*)?(?:experience|exp|working)'
            match = re.search(year_pattern, text, re.IGNORECASE)
            if match:
                total_years = float(match.group(1))
        
        return total_years
    
    def extract_experience(self, text: str) -> List[Dict]:
        """Extract work experience from resume"""
        experiences = []
        
        # Split by common experience section headers
        sections = re.split(
            r'(?:EXPERIENCE|WORK EXPERIENCE|EMPLOYMENT|PROFESSIONAL EXPERIENCE|WORK HISTORY)',
            text,
            flags=re.IGNORECASE
        )
        
        if len(sections) > 1:
            exp_text = sections[1]
            
            # Split by common delimiters for entries
            entries = re.split(r'(?:\n\n|\n(?=[A-Z][a-z])|(?:^|\n)[-•*])', exp_text)
            
            for entry in entries[:10]:  # Limit to 10 entries
                if len(entry.strip()) < 20:
                    continue
                
                # Extract company
                company_match = re.search(
                    r'(?:at\s+|,\s*|^)([A-Z][A-Za-z\s&.-]+?)(?:,|\||$)',
                    entry.split('\n')[0]
                )
                company = company_match.group(1).strip() if company_match else "Unknown"
                
                # Extract role
                role_patterns = [
                    r'([A-Z][a-zA-Z\s]+(?:Engineer|Developer|Manager|Analyst|Architect|Specialist))',
                    r'^([A-Za-z\s]+)(?:,|at)',
                ]
                role = "Unknown"
                for pattern in role_patterns:
                    role_match = re.search(pattern, entry)
                    if role_match:
                        role = role_match.group(1).strip()
                        break
                
                # Extract dates and duration
                date_pattern = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*\d{2,4}|(\d{1,2})/(\d{1,2})/(\d{4})|(\d{4})'
                dates = re.findall(date_pattern, entry, re.IGNORECASE)
                
                duration_years = None
                duration_match = re.search(r'(\d+)\s*(?:years?|yrs?)', entry, re.IGNORECASE)
                if duration_match:
                    duration_years = float(duration_match.group(1))
                
                # Extract bullet points (skills/responsibilities)
                bullets = re.findall(r'(?:^|\n)\s*[-•*]\s*(.+?)(?=\n|$)', entry, re.MULTILINE)
                description = " ".join(bullets) if bullets else entry.split('\n')[1] if len(entry.split('\n')) > 1 else ""
                
                # Extract skills mentioned
                skills_used = self._extract_skills_from_context(description)
                
                experiences.append({
                    'company': company,
                    'role': role,
                    'duration_years': duration_years,
                    'description': description[:200],  # Limit description length
                    'skills_used': skills_used
                })
        
        return experiences
    
    def extract_education(self, text: str) -> List[Dict]:
        """Extract education from resume"""
        education_entries = []
        
        sections = re.split(
            r'(?:EDUCATION|TRAINING|QUALIFICATIONS|ACADEMIC)',
            text,
            flags=re.IGNORECASE
        )
        
        if len(sections) > 1:
            edu_text = sections[1]
            entries = re.split(r'(?:\n\n|\n(?=[A-Z]))', edu_text)
            
            for entry in entries[:5]:  # Limit to 5 entries
                if len(entry.strip()) < 10:
                    continue
                
                # Extract degree type
                degree = "Unknown"
                for edu_keyword in ["B.S.", "B.A.", "B.Tech", "M.S.", "M.Tech", "Ph.D.", "MBA"]:
                    if edu_keyword in entry:
                        degree = edu_keyword
                        break
                
                # Extract institution
                institution_match = re.search(
                    r'(?:from|,|\||^)\s*([A-Z][A-Za-z\s,&-]+(?:University|College|Institute|School))',
                    entry
                )
                institution = institution_match.group(1).strip() if institution_match else "Unknown"
                
                # Extract years
                year_pattern = r'\b(19|20)\d{2}\b'
                years = re.findall(year_pattern, entry)
                
                gpa_match = re.search(r'(?:GPA|gpa)[\s:]*(\d\.\d{1,2})', entry)
                gpa = float(gpa_match.group(1)) if gpa_match else None
                
                education_entries.append({
                    'institution': institution,
                    'degree': degree,
                    'field_of_study': entry.split('\n')[1] if len(entry.split('\n')) > 1 else None,
                    'gpa': gpa
                })
        
        return education_entries
    
    def extract_projects(self, text: str) -> List[Dict]:
        """Extract projects from resume"""
        projects = []
        
        sections = re.split(
            r'(?:PROJECTS?|PORTFOLIO)',
            text,
            flags=re.IGNORECASE
        )
        
        if len(sections) > 1:
            proj_text = sections[1]
            entries = re.split(r'(?:\n\n|\n(?=[A-Z])|[-•*])', proj_text)
            
            for entry in entries[:5]:  # Limit to 5 projects
                if len(entry.strip()) < 15:
                    continue
                
                # Project name is usually first line
                lines = entry.strip().split('\n')
                name = lines[0][:100]
                
                # Description
                description = " ".join(lines[1:]) if len(lines) > 1 else ""
                
                # Technologies
                tech_match = re.search(
                    r'(?:(?:Built|Created|Developed|Used)\s+(?:with|using|in):|Skills?:)\s*(.+?)(?:\n|$)',
                    entry,
                    re.IGNORECASE
                )
                technologies = [t.strip() for t in tech_match.group(1).split(',')] if tech_match else []
                
                projects.append({
                    'name': name,
                    'description': description[:200],
                    'technologies': technologies
                })
        
        return projects
    
    def _extract_skills_from_context(self, context: str) -> List[str]:
        """Extract skills mentioned in a given context"""
        # Common technical skills
        common_skills = {
            'programming': ['python', 'java', 'javascript', 'c++', 'c#', 'go', 'rust', 'php', 'ruby', 'scala', 'kotlin'],
            'web': ['react', 'angular', 'vue', 'node', 'express', 'django', 'flask', 'spring', 'asp.net'],
            'database': ['sql', 'mongodb', 'postgresql', 'mysql', 'oracle', 'dynamodb', 'redis', 'elasticsearch'],
            'cloud': ['aws', 'azure', 'gcp', 'kubernetes', 'docker', 'jenkins', 'terraform'],
            'data': ['pandas', 'numpy', 'tensorflow', 'pytorch', 'scikit-learn', 'spark', 'hadoop'],
        }
        
        skills_found = []
        context_lower = context.lower()
        
        for category, skills in common_skills.items():
            for skill in skills:
                if skill in context_lower:
                    skills_found.append(skill.title())
        
        return list(set(skills_found))  # Remove duplicates
    
    def parse_resume(self, file_content: str, file_format: str, candidate_name: Optional[str] = None) -> Dict:
        """
        Main method to parse resume and extract all information
        Returns complete structured resume data
        """
        # Convert to text
        text = self.convert_file_to_text(file_content, file_format)
        
        if not text:
            logger.error("Failed to extract text from resume")
            return {
                'success': False,
                'error': 'Failed to extract text from resume',
                'extraction_confidence': 0.0
            }
        
        try:
            # Extract all components
            name = candidate_name or self.extract_name(text)
            email = self.extract_email(text)
            phone = self.extract_phone(text)
            experience = self.extract_experience(text)
            education = self.extract_education(text)
            projects = self.extract_projects(text)
            years_of_experience = self.extract_years_of_experience(text, experience)
            
            # Calculate extraction confidence (based on what was extracted)
            extracted_fields = sum([
                bool(name),
                bool(email),
                bool(phone),
                len(experience) > 0,
                len(education) > 0,
                years_of_experience > 0
            ])
            extraction_confidence = extracted_fields / 6.0  # 6 main components
            
            return {
                'success': True,
                'name': name or "Unknown",
                'email': email,
                'phone': phone,
                'years_of_experience': years_of_experience,
                'experience': experience,
                'education': education,
                'projects': projects,
                'resume_text': text[:5000],  # Store first 5000 chars
                'extraction_confidence': extraction_confidence,
                'parse_timestamp': datetime.utcnow()
            }
        
        except Exception as e:
            logger.error(f"Error during resume parsing: {e}")
            return {
                'success': False,
                'error': str(e),
                'extraction_confidence': 0.0
            }
