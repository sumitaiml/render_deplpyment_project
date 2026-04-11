"""
Sample data and test fixtures for development and demo purposes
"""

SAMPLE_RESUME_TEXT = """
JOHN DOE
john.doe@techmail.com | (555) 123-4567 | linkedin.com/in/johndoe

PROFESSIONAL SUMMARY
Experienced Full Stack Engineer with 5 years of expertise in building scalable web applications 
and microservices. Proficient in Python, Java, and modern frontend frameworks. Strong background 
in cloud architecture and DevOps practices. Led cross-functional teams to deliver high-impact solutions.

TECHNICAL SKILLS
Programming Languages: Python, Java, JavaScript, TypeScript, Go
Web Frameworks: React, Node.js, Spring Boot, Django, Flask
Databases: PostgreSQL, MongoDB, Redis, Elasticsearch
Cloud & DevOps: AWS (EC2, S3, Lambda), Docker, Kubernetes, Terraform, Jenkins
Tools & Platforms: Git, GitHub, Jira, Docker, Kubernetes, CI/CD

PROFESSIONAL EXPERIENCE

Senior Software Engineer - TechCorp Inc.
March 2021 - Present (3 years)
• Led team of 5 engineers on microservices migration project, reducing deployment time by 60%
• Architected REST APIs and designed database schemas for real-time data processing
• Implemented CI/CD pipelines using Jenkins and Docker, improving code quality
• Mentored 3 junior developers on system design and best practices

Software Engineer - StartupXYZ
June 2019 - February 2021 (1.8 years)
• Developed full-stack features for SaaS platform using React and Django
• Built and optimized PostgreSQL databases handling 1M+ daily transactions
• Containerized applications using Docker and deployed on Kubernetes
• Implemented caching layer with Redis, improving API response time by 45%

Junior Developer - LocalTech Solutions
July 2018 - May 2019 (1 year)
• Developed backend services using Python and Flask
• Assisted in migrating legacy systems to microservices architecture
• Contributed to open-source projects

EDUCATION

Bachelor of Science in Computer Science
State University - Graduated May 2018
GPA: 3.7/4.0

PROJECTS & ACHIEVEMENTS
• Built distributed system processing 10M events/day using Kafka and Spark
• Open source contributor - 2K+ GitHub stars on web framework library
• AWS Certified Solutions Architect

CERTIFICATIONS
• AWS Certified Solutions Architect - Professional
• Kubernetes Application Developer (CKAD)
"""

SAMPLE_JOB_DESCRIPTION = """
JOB TITLE: Senior Backend Engineer

ABOUT THE ROLE
We're looking for a Senior Backend Engineer to join our platform team. You'll work on 
high-scale distributed systems and mentor junior engineers.

KEY RESPONSIBILITIES
- Design and implement microservices architecture
- Build REST APIs and optimize database queries
- Lead technical design discussions and code reviews
- Collaborate with frontend and DevOps teams
- Mentor junior engineers

REQUIRED SKILLS
- 5+ years software engineering experience
- Expert in Python or Java
- Strong understanding of microservices and distributed systems
- Experience with SQL and NoSQL databases
- Proficiency with Docker and Kubernetes
- AWS or similar cloud platform experience

PREFERRED SKILLS
- Experience with message queues (Kafka, RabbitMQ)
- Knowledge of GraphQL
- Open source contributions
- Agile methodology experience
- Experience with ML/AI systems

COMPENSATION & BENEFITS
- Competitive salary: $150k-$200k
- Stock options
- 401(k) matching
- Health insurance
- Remote-friendly
- Professional development budget
"""

SAMPLE_CANDIDATES = [
    {
        "name": "Alice Johnson",
        "email": "alice@email.com",
        "experience_years": 6,
        "seniority": "senior",
        "skills": ["Python", "Java", "REST API", "PostgreSQL", "Docker", "Kubernetes", "AWS"],
        "expected_score": 88
    },
    {
        "name": "Bob Smith",
        "email": "bob@email.com",
        "experience_years": 4,
        "seniority": "mid_level",
        "skills": ["Python", "React", "MongoDB", "Docker"],
        "expected_score": 65
    },
    {
        "name": "Carol Davis",
        "email": "carol@email.com",
        "experience_years": 8,
        "seniority": "senior",
        "skills": ["Java", "Spring Boot", "PostgreSQL", "Kafka", "Kubernetes", "GCP", "System Design"],
        "expected_score": 85
    },
    {
        "name": "David Lee",
        "email": "david@email.com",
        "experience_years": 2,
        "seniority": "junior",
        "skills": ["Python", "Flask", "PostgreSQL", "JavaScript"],
        "expected_score": 45
    }
]

SAMPLE_SKILL_ONTOLOGY = {
    "skills": {
        "Python": {"category": "Programming Language", "level": 1},
        "Java": {"category": "Programming Language", "level": 1},
        "REST API": {"category": "Architecture", "level": 2},
        "PostgreSQL": {"category": "Database", "level": 2},
        "Docker": {"category": "DevOps", "level": 2},
        "Kubernetes": {"category": "DevOps", "level": 2},
        "AWS": {"category": "Cloud", "level": 2},
        "Microservices": {"category": "Architecture", "level": 2},
        "System Design": {"category": "Architecture", "level": 3},
    },
    "relationships": {
        "Spring Boot->Java": {"type": "requires", "strength": 0.95},
        "Python->Backend": {"type": "implies", "strength": 0.85},
        "Docker->DevOps": {"type": "implies", "strength": 0.80},
        "Kubernetes->Docker": {"type": "related_to", "strength": 0.85},
    }
}

def generate_sample_resume_json():
    """Generate sample parsed resume JSON"""
    return {
        'name': 'John Doe',
        'email': 'john.doe@techmail.com',
        'phone': '(555) 123-4567',
        'years_of_experience': 5.0,
        'experience': [
            {
                'company': 'TechCorp Inc.',
                'role': 'Senior Software Engineer',
                'duration_years': 3,
                'description': 'Led team on microservices migration, architected REST APIs'
            },
            {
                'company': 'StartupXYZ',
                'role': 'Software Engineer',
                'duration_years': 1.8,
                'description': 'Developed full-stack features, optimized databases'
            }
        ],
        'education': [
            {
                'institution': 'State University',
                'degree': 'B.S.',
                'field_of_study': 'Computer Science',
                'gpa': 3.7
            }
        ],
        'projects': [
            {
                'name': 'Distributed System',
                'description': 'Event processing system handling 10M events/day',
                'technologies': ['Kafka', 'Spark', 'Python']
            }
        ],
        'skills': [
            {'skill': 'Python', 'proficiency_level': 'expert', 'confidence_score': 0.95},
            {'skill': 'Java', 'proficiency_level': 'advanced', 'confidence_score': 0.90},
            {'skill': 'REST API', 'proficiency_level': 'expert', 'confidence_score': 0.95},
            {'skill': 'PostgreSQL', 'proficiency_level': 'advanced', 'confidence_score': 0.90},
            {'skill': 'Docker', 'proficiency_level': 'expert', 'confidence_score': 0.95},
            {'skill': 'Kubernetes', 'proficiency_level': 'advanced', 'confidence_score': 0.85},
            {'skill': 'AWS', 'proficiency_level': 'advanced', 'confidence_score': 0.85},
        ]
    }

if __name__ == "__main__":
    print("=== SAMPLE DATA FOR HRTECH PLATFORM ===\n")
    print("Resume Text (for testing):")
    print(SAMPLE_RESUME_TEXT[:300] + "...\n")
    print(f"Job Description (for testing):")
    print(SAMPLE_JOB_DESCRIPTION[:300] + "...\n")
    print(f"Sample Candidates: {len(SAMPLE_CANDIDATES)} candidates")
    for c in SAMPLE_CANDIDATES:
        print(f"  - {c['name']}: {c['seniority']} ({c['experience_years']} years)")
