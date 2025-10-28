#!/usr/bin/env python3
"""
Convert text files to PDFs for RAG system testing
Creates professional-looking PDFs from markdown and text content
"""

import os
from pathlib import Path
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.colors import black, blue, darkblue
import markdown
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFGenerator:
    """Generate professional PDFs from text content"""
    
    def __init__(self, output_dir: str = "datasets/pdfs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()
    
    def _setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Title style
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=darkblue,
            alignment=1  # Center alignment
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=12,
            textColor=blue,
            keepWithNext=1
        ))
        
        # Subheading style
        self.styles.add(ParagraphStyle(
            name='CustomSubheading',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=10,
            textColor=darkblue,
            keepWithNext=1
        ))
        
        # Body text style
        self.styles.add(ParagraphStyle(
            name='CustomBody',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=8,
            leading=14
        ))
    
    def create_medical_pdfs(self):
        """Create medical knowledge PDFs"""
        logger.info("Creating medical knowledge PDFs...")
        
        # Medical AI and Healthcare Technology
        medical_ai_content = """
# Medical AI and Healthcare Technology

## Introduction
Artificial Intelligence is transforming healthcare delivery through innovative applications that enhance patient care, improve diagnostic accuracy, and streamline clinical workflows.

## Key Applications

### Diagnostic Imaging
- **Radiology**: AI algorithms can detect abnormalities in X-rays, CT scans, and MRIs with high accuracy
- **Pathology**: Computer vision systems assist in analyzing tissue samples and identifying cancer cells
- **Ophthalmology**: Automated screening for diabetic retinopathy and age-related macular degeneration

### Clinical Decision Support
- **Risk Assessment**: Predictive models identify patients at risk for complications
- **Treatment Recommendations**: AI systems suggest optimal treatment protocols based on patient data
- **Drug Interactions**: Automated checking for potential adverse drug reactions

### Natural Language Processing
- **Clinical Documentation**: Automated extraction of information from medical records
- **Literature Review**: AI-powered analysis of medical research papers
- **Patient Communication**: Chatbots for initial symptom assessment and triage

## Implementation Considerations

### Data Quality and Privacy
- Ensure HIPAA compliance for all patient data
- Implement robust data governance frameworks
- Maintain high-quality, diverse training datasets

### Clinical Validation
- Conduct rigorous clinical trials for AI systems
- Establish clear performance metrics and benchmarks
- Ensure regulatory approval from FDA and other bodies

### Integration Challenges
- Seamless integration with existing Electronic Health Records (EHR)
- Training healthcare professionals on AI tools
- Managing workflow disruptions during implementation

## Future Directions

### Personalized Medicine
- Genomic analysis for targeted therapies
- Precision dosing based on individual patient characteristics
- Customized treatment plans using multi-modal data

### Preventive Care
- Early disease detection through continuous monitoring
- Population health management and risk stratification
- Lifestyle intervention recommendations

### Global Health Impact
- Telemedicine and remote patient monitoring
- AI-powered diagnostics in resource-limited settings
- Epidemic surveillance and outbreak prediction

## Ethical Considerations
- Algorithmic bias and health equity
- Transparency and explainability in AI decisions
- Patient consent and data ownership rights
- Professional liability and accountability frameworks
"""

        # Clinical Guidelines and Best Practices
        clinical_guidelines_content = """
# Clinical Guidelines and Best Practices

## Evidence-Based Medicine

### Systematic Reviews and Meta-Analyses
Evidence-based medicine relies on the systematic evaluation of research evidence to guide clinical decision-making.

#### Key Principles
- **Hierarchy of Evidence**: Randomized controlled trials and systematic reviews provide the strongest evidence
- **Critical Appraisal**: Systematic evaluation of study quality and methodology
- **Clinical Applicability**: Translating research findings to individual patient care

### Guidelines Development Process
- Literature review and evidence synthesis
- Expert consensus and stakeholder input
- Peer review and validation
- Regular updates based on new evidence

## Patient Safety and Quality Improvement

### Medication Safety
- **Five Rights**: Right patient, medication, dose, route, and time
- **Reconciliation**: Accurate medication lists across care transitions
- **Adverse Event Reporting**: Systematic tracking and analysis of medication errors

### Infection Control
- **Hand Hygiene**: Primary prevention measure for healthcare-associated infections
- **Isolation Precautions**: Standard and transmission-based precautions
- **Antimicrobial Stewardship**: Optimizing antibiotic use to combat resistance

### Patient Identification
- **Two-Patient Identifiers**: Name and date of birth or medical record number
- **Verification Procedures**: Confirming patient identity before procedures
- **Wristband Protocols**: Standardized patient identification systems

## Chronic Disease Management

### Diabetes Care
- **Glycemic Control**: HbA1c targets and monitoring protocols
- **Complication Screening**: Regular assessment for diabetic complications
- **Patient Education**: Self-management training and support

### Cardiovascular Disease
- **Risk Assessment**: Using validated risk calculators
- **Lifestyle Modifications**: Diet, exercise, and smoking cessation
- **Medication Management**: Evidence-based pharmacotherapy

### Mental Health Integration
- **Screening Protocols**: Regular assessment for depression and anxiety
- **Collaborative Care Models**: Integration of mental health services
- **Crisis Intervention**: Procedures for managing psychiatric emergencies

## Quality Metrics and Outcomes

### Clinical Indicators
- **Process Measures**: Adherence to evidence-based practices
- **Outcome Measures**: Patient health outcomes and functional status
- **Patient Experience**: Satisfaction surveys and feedback mechanisms

### Performance Improvement
- **Plan-Do-Study-Act (PDSA) Cycles**: Systematic approach to quality improvement
- **Root Cause Analysis**: Investigation of adverse events and near misses
- **Benchmarking**: Comparison with national and international standards
"""

        # Public Health and Epidemiology
        public_health_content = """
# Public Health and Epidemiology

## Epidemiological Principles

### Disease Surveillance
Public health surveillance is the ongoing systematic collection, analysis, and interpretation of health data essential to planning, implementation, and evaluation of public health practice.

#### Surveillance Systems
- **Passive Surveillance**: Routine reporting by healthcare providers
- **Active Surveillance**: Proactive case finding by public health officials
- **Sentinel Surveillance**: Monitoring specific populations or conditions

### Outbreak Investigation
- **Case Definition**: Establishing criteria for identifying cases
- **Descriptive Epidemiology**: Person, place, and time analysis
- **Analytical Studies**: Case-control and cohort studies to identify risk factors

## Preventive Medicine

### Primary Prevention
- **Vaccination Programs**: Immunization schedules and coverage targets
- **Health Promotion**: Lifestyle interventions and behavior change
- **Environmental Health**: Reducing exposure to health hazards

### Secondary Prevention
- **Screening Programs**: Early detection of disease in asymptomatic populations
- **Risk Assessment**: Identifying individuals at high risk for disease
- **Diagnostic Testing**: Appropriate use of screening tests

### Tertiary Prevention
- **Disease Management**: Preventing complications in those with established disease
- **Rehabilitation**: Restoring function and preventing disability
- **Palliative Care**: Improving quality of life for those with serious illness

## Global Health Challenges

### Infectious Diseases
- **Emerging Pathogens**: Surveillance and response to new infectious threats
- **Antimicrobial Resistance**: Strategies to combat drug-resistant organisms
- **Vector-Borne Diseases**: Control of mosquito-borne and tick-borne illnesses

### Non-Communicable Diseases
- **Cardiovascular Disease**: Leading cause of death globally
- **Cancer Prevention**: Screening and risk reduction strategies
- **Diabetes Epidemic**: Prevention and management of type 2 diabetes

### Health Equity
- **Social Determinants**: Addressing root causes of health disparities
- **Access to Care**: Ensuring equitable access to healthcare services
- **Cultural Competency**: Providing culturally appropriate care

## Environmental Health

### Air Quality
- **Pollution Monitoring**: Tracking air quality indicators
- **Health Impact Assessment**: Evaluating effects of air pollution on health
- **Policy Interventions**: Regulations to reduce emissions

### Water Safety
- **Drinking Water Standards**: Ensuring safe water supply
- **Waterborne Disease Prevention**: Monitoring and preventing contamination
- **Sanitation Systems**: Proper waste management and treatment

### Climate Change and Health
- **Heat-Related Illness**: Preparing for extreme temperature events
- **Vector Ecology**: Changes in disease vector distribution
- **Food Security**: Impact of climate change on nutrition and food safety
"""

        # Create PDFs
        pdfs_to_create = [
            ("medical_ai_healthcare_technology.pdf", medical_ai_content),
            ("clinical_guidelines_best_practices.pdf", clinical_guidelines_content),
            ("public_health_epidemiology.pdf", public_health_content)
        ]
        
        for filename, content in pdfs_to_create:
            self._create_pdf_from_markdown(content, filename)
    
    def create_technical_pdfs(self):
        """Create technical documentation PDFs"""
        logger.info("Creating technical documentation PDFs...")
        
        # RAG Systems Implementation
        rag_systems_content = """
# RAG Systems: Implementation and Best Practices

## Introduction to RAG
Retrieval-Augmented Generation (RAG) represents a paradigm shift in how we build AI systems that can access and utilize external knowledge.

## Architecture Overview

### Core Components
- **Document Processing Pipeline**: Text extraction, chunking, and preprocessing
- **Vector Database**: Efficient storage and retrieval of embeddings
- **Retrieval System**: Query processing and similarity search
- **Generation Model**: Large language model for response synthesis

### Data Flow
1. **Ingestion**: Documents are processed and converted to embeddings
2. **Storage**: Embeddings are stored in vector database with metadata
3. **Query**: User queries are converted to embeddings
4. **Retrieval**: Similar documents are retrieved based on vector similarity
5. **Generation**: LLM generates response using retrieved context

## Implementation Strategies

### Document Processing
- **Text Extraction**: Handling various file formats (PDF, DOCX, HTML)
- **Chunking Strategies**: Optimal chunk size (500-1500 tokens)
- **Overlap Management**: Maintaining context across chunks
- **Metadata Preservation**: Tracking source information and structure

### Embedding Models
- **Model Selection**: Choosing appropriate embedding models
- **Fine-tuning**: Domain-specific embedding optimization
- **Multilingual Support**: Handling multiple languages
- **Dimensionality Considerations**: Balancing performance and storage

### Vector Databases
- **Pinecone**: Managed vector database service
- **Weaviate**: Open-source vector search engine
- **Chroma**: Lightweight vector database for development
- **FAISS**: Facebook's similarity search library

## Advanced Techniques

### Hybrid Search
- **Keyword + Semantic**: Combining traditional and vector search
- **Reranking**: Improving retrieval quality with cross-encoders
- **Query Expansion**: Enhancing queries for better retrieval

### Context Management
- **Window Size**: Managing LLM context limitations
- **Context Compression**: Summarizing retrieved documents
- **Multi-hop Reasoning**: Handling complex queries requiring multiple retrievals

### Quality Assurance
- **Evaluation Metrics**: BLEU, ROUGE, and custom metrics
- **Human Evaluation**: Expert assessment of response quality
- **A/B Testing**: Comparing different RAG configurations

## Performance Optimization

### Retrieval Optimization
- **Index Tuning**: Optimizing vector database performance
- **Caching Strategies**: Reducing latency for common queries
- **Batch Processing**: Efficient handling of multiple queries

### Generation Optimization
- **Model Selection**: Choosing appropriate LLMs
- **Prompt Engineering**: Crafting effective system prompts
- **Temperature Tuning**: Balancing creativity and accuracy

### Scalability Considerations
- **Horizontal Scaling**: Distributing load across multiple instances
- **Load Balancing**: Managing traffic distribution
- **Resource Management**: Optimizing compute and memory usage

## Common Challenges and Solutions

### Hallucination Mitigation
- **Source Attribution**: Clearly citing retrieved information
- **Confidence Scoring**: Indicating uncertainty in responses
- **Fact Checking**: Implementing verification mechanisms

### Retrieval Quality
- **Relevance Tuning**: Improving similarity search accuracy
- **Diversity**: Ensuring diverse perspectives in retrieved content
- **Freshness**: Managing temporal aspects of information

### User Experience
- **Response Time**: Optimizing for low latency
- **Transparency**: Showing sources and reasoning
- **Personalization**: Adapting to user preferences and context
"""

        # Machine Learning Operations
        mlops_content = """
# Machine Learning Operations (MLOps)

## MLOps Fundamentals

### Definition and Scope
MLOps is a set of practices that aims to deploy and maintain machine learning models in production reliably and efficiently.

#### Key Principles
- **Automation**: Automated pipelines for training, testing, and deployment
- **Reproducibility**: Consistent results across different environments
- **Monitoring**: Continuous observation of model performance
- **Collaboration**: Seamless cooperation between data scientists and engineers

### MLOps Lifecycle
1. **Data Management**: Collection, validation, and versioning
2. **Model Development**: Experimentation and training
3. **Model Validation**: Testing and evaluation
4. **Deployment**: Production deployment and serving
5. **Monitoring**: Performance tracking and alerting
6. **Maintenance**: Updates, retraining, and optimization

## Infrastructure and Tools

### Version Control
- **Git**: Code versioning and collaboration
- **DVC**: Data and model versioning
- **MLflow**: Experiment tracking and model registry

### Containerization
- **Docker**: Application containerization
- **Kubernetes**: Container orchestration
- **Helm**: Kubernetes package management

### Cloud Platforms
- **AWS SageMaker**: End-to-end ML platform
- **Google Cloud AI Platform**: Integrated ML services
- **Azure Machine Learning**: Comprehensive ML lifecycle management

## Data Pipeline Management

### Data Ingestion
- **Batch Processing**: Scheduled data processing jobs
- **Stream Processing**: Real-time data ingestion
- **Data Quality Checks**: Validation and anomaly detection

### Feature Engineering
- **Feature Stores**: Centralized feature management
- **Pipeline Orchestration**: Workflow management tools
- **Data Lineage**: Tracking data transformations

### Data Governance
- **Privacy Compliance**: GDPR, CCPA, and other regulations
- **Access Control**: Role-based data access
- **Audit Trails**: Comprehensive logging and monitoring

## Model Development and Training

### Experiment Management
- **Hyperparameter Tuning**: Automated optimization
- **Model Comparison**: A/B testing frameworks
- **Reproducible Environments**: Consistent development setups

### Training Infrastructure
- **Distributed Training**: Multi-GPU and multi-node training
- **Resource Management**: Efficient compute utilization
- **Cost Optimization**: Spot instances and preemptible VMs

### Model Validation
- **Cross-Validation**: Robust model evaluation
- **Bias Detection**: Fairness and equity assessment
- **Performance Metrics**: Comprehensive evaluation frameworks

## Deployment Strategies

### Deployment Patterns
- **Blue-Green Deployment**: Zero-downtime deployments
- **Canary Releases**: Gradual rollout to production
- **A/B Testing**: Comparing model performance

### Serving Infrastructure
- **Model Serving**: REST APIs and gRPC services
- **Load Balancing**: Traffic distribution and scaling
- **Caching**: Response caching for improved performance

### Edge Deployment
- **Mobile Deployment**: On-device model inference
- **IoT Integration**: Edge computing for real-time processing
- **Offline Capabilities**: Models that work without internet connectivity

## Monitoring and Maintenance

### Performance Monitoring
- **Model Drift**: Detecting changes in data distribution
- **Prediction Quality**: Tracking accuracy and other metrics
- **System Health**: Infrastructure monitoring and alerting

### Continuous Integration/Continuous Deployment (CI/CD)
- **Automated Testing**: Unit tests, integration tests, and model tests
- **Pipeline Automation**: Automated training and deployment
- **Rollback Strategies**: Quick recovery from failed deployments

### Model Governance
- **Model Registry**: Centralized model management
- **Compliance Tracking**: Regulatory requirement adherence
- **Documentation**: Comprehensive model documentation
"""

        # Create technical PDFs
        tech_pdfs = [
            ("rag_systems_implementation.pdf", rag_systems_content),
            ("mlops_best_practices.pdf", mlops_content)
        ]
        
        for filename, content in tech_pdfs:
            self._create_pdf_from_markdown(content, filename)
    
    def create_business_pdfs(self):
        """Create business and compliance PDFs"""
        logger.info("Creating business and compliance PDFs...")
        
        # Data Privacy and Compliance
        privacy_compliance_content = """
# Data Privacy and Compliance Framework

## Regulatory Landscape

### General Data Protection Regulation (GDPR)
The GDPR is a comprehensive data protection law that applies to organizations processing personal data of EU residents.

#### Key Principles
- **Lawfulness, Fairness, and Transparency**: Processing must be lawful and transparent
- **Purpose Limitation**: Data must be collected for specified, explicit purposes
- **Data Minimization**: Only necessary data should be processed
- **Accuracy**: Personal data must be accurate and up to date
- **Storage Limitation**: Data should not be kept longer than necessary
- **Integrity and Confidentiality**: Appropriate security measures must be implemented

#### Individual Rights
- **Right to Information**: Clear information about data processing
- **Right of Access**: Individuals can request copies of their data
- **Right to Rectification**: Correction of inaccurate personal data
- **Right to Erasure**: "Right to be forgotten" under certain circumstances
- **Right to Restrict Processing**: Limiting how data is used
- **Right to Data Portability**: Transferring data between services
- **Right to Object**: Objecting to certain types of processing

### Health Insurance Portability and Accountability Act (HIPAA)
HIPAA establishes national standards for protecting patient health information in the United States.

#### Covered Entities
- Healthcare providers
- Health plans
- Healthcare clearinghouses
- Business associates

#### Privacy Rule
- **Minimum Necessary Standard**: Use and disclose only the minimum necessary PHI
- **Individual Rights**: Patients' rights to access and control their health information
- **Administrative Requirements**: Policies, procedures, and training

#### Security Rule
- **Administrative Safeguards**: Security officer, workforce training, access management
- **Physical Safeguards**: Facility access controls, workstation use restrictions
- **Technical Safeguards**: Access control, audit controls, integrity, transmission security

## Risk Management Framework

### Risk Assessment
- **Asset Identification**: Cataloging data assets and systems
- **Threat Analysis**: Identifying potential security threats
- **Vulnerability Assessment**: Evaluating system weaknesses
- **Impact Analysis**: Assessing potential consequences of breaches

### Risk Mitigation Strategies
- **Preventive Controls**: Measures to prevent security incidents
- **Detective Controls**: Systems to identify security breaches
- **Corrective Controls**: Procedures to respond to incidents
- **Compensating Controls**: Alternative measures when primary controls fail

### Business Continuity Planning
- **Disaster Recovery**: Procedures for system recovery
- **Data Backup**: Regular backup and restoration testing
- **Incident Response**: Coordinated response to security incidents
- **Communication Plans**: Stakeholder notification procedures

## Compliance Implementation

### Governance Structure
- **Data Protection Officer (DPO)**: Oversight and compliance monitoring
- **Privacy Committee**: Cross-functional privacy governance
- **Compliance Team**: Legal and regulatory expertise
- **Technical Teams**: Implementation and maintenance

### Policy Development
- **Privacy Policies**: Clear, accessible privacy notices
- **Data Handling Procedures**: Detailed operational procedures
- **Incident Response Plans**: Step-by-step response procedures
- **Training Programs**: Regular staff education and awareness

### Documentation Requirements
- **Data Processing Records**: Comprehensive processing documentation
- **Impact Assessments**: Privacy and security impact evaluations
- **Consent Management**: Records of consent and preferences
- **Audit Trails**: Detailed logs of data access and processing

## Technology Implementation

### Privacy by Design
- **Proactive Measures**: Anticipating and preventing privacy invasions
- **Default Settings**: Privacy-friendly default configurations
- **Full Functionality**: Accommodating all legitimate interests
- **End-to-End Security**: Secure data lifecycle management

### Data Protection Technologies
- **Encryption**: Data protection at rest and in transit
- **Anonymization**: Removing personally identifiable information
- **Pseudonymization**: Replacing identifying information with pseudonyms
- **Access Controls**: Role-based access management

### Monitoring and Auditing
- **Continuous Monitoring**: Real-time privacy and security monitoring
- **Regular Audits**: Periodic compliance assessments
- **Penetration Testing**: Security vulnerability testing
- **Third-Party Assessments**: Independent compliance evaluations
"""

        # Create business PDF
        business_pdfs = [
            ("data_privacy_compliance_framework.pdf", privacy_compliance_content)
        ]
        
        for filename, content in business_pdfs:
            self._create_pdf_from_markdown(content, filename)
    
    def _create_pdf_from_markdown(self, content: str, filename: str):
        """Convert markdown content to PDF"""
        try:
            output_path = self.output_dir / filename
            
            # Create PDF document
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Parse content and create story
            story = []
            lines = content.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 12))
                elif line.startswith('# '):
                    # Main title
                    title = line[2:].strip()
                    story.append(Paragraph(title, self.styles['CustomTitle']))
                    story.append(Spacer(1, 20))
                elif line.startswith('## '):
                    # Section heading
                    heading = line[3:].strip()
                    story.append(Paragraph(heading, self.styles['CustomHeading']))
                    story.append(Spacer(1, 12))
                elif line.startswith('### '):
                    # Subsection heading
                    subheading = line[4:].strip()
                    story.append(Paragraph(subheading, self.styles['CustomSubheading']))
                    story.append(Spacer(1, 8))
                elif line.startswith('#### '):
                    # Sub-subsection heading
                    subheading = line[5:].strip()
                    story.append(Paragraph(f"<b>{subheading}</b>", self.styles['CustomBody']))
                    story.append(Spacer(1, 6))
                elif line.startswith('- ') or line.startswith('* '):
                    # Bullet point
                    bullet_text = line[2:].strip()
                    story.append(Paragraph(f"• {bullet_text}", self.styles['CustomBody']))
                elif line.startswith('1. ') or any(line.startswith(f"{i}. ") for i in range(1, 10)):
                    # Numbered list
                    story.append(Paragraph(line, self.styles['CustomBody']))
                else:
                    # Regular paragraph
                    if line:
                        # Handle bold text
                        line = line.replace('**', '<b>').replace('**', '</b>')
                        story.append(Paragraph(line, self.styles['CustomBody']))
            
            # Add footer with generation date
            story.append(Spacer(1, 30))
            story.append(Paragraph(
                f"<i>Generated on {datetime.now().strftime('%B %d, %Y')}</i>",
                self.styles['Normal']
            ))
            
            # Build PDF
            doc.build(story)
            logger.info(f"Created PDF: {filename}")
            
        except Exception as e:
            logger.error(f"Failed to create PDF {filename}: {str(e)}")

def main():
    """Main execution function"""
    generator = PDFGenerator()
    
    print("🚀 Creating Professional Dataset PDFs...")
    print("Choose dataset type:")
    print("1. Medical Knowledge PDFs")
    print("2. Technical Documentation PDFs") 
    print("3. Business & Compliance PDFs")
    print("4. All PDF Datasets")
    
    choice = input("Enter your choice (1-4): ").strip()
    
    if choice == "1":
        generator.create_medical_pdfs()
    elif choice == "2":
        generator.create_technical_pdfs()
    elif choice == "3":
        generator.create_business_pdfs()
    elif choice == "4":
        generator.create_medical_pdfs()
        generator.create_technical_pdfs()
        generator.create_business_pdfs()
    else:
        print("Invalid choice. Creating all PDFs...")
        generator.create_medical_pdfs()
        generator.create_technical_pdfs()
        generator.create_business_pdfs()
    
    print("\n" + "="*60)
    print("📚 PDF DATASET CREATION COMPLETE!")
    print("="*60)
    print(f"📁 PDFs created in: {generator.output_dir}")
    print("\n🎯 Next Steps:")
    print("1. Navigate to the 'datasets/pdfs' folder")
    print("2. Upload the PDFs to your RAG system at http://localhost:5173")
    print("3. Go to the 'Upload' tab and drag-and-drop the PDF files")
    print("4. Test queries in the 'Chat' tab")
    print("\n💡 Sample Questions to Try:")
    print("- 'What is RAG and how does it work?'")
    print("- 'Explain GDPR compliance requirements'")
    print("- 'What are the key principles of medical AI?'")
    print("- 'How do you implement MLOps best practices?'")

if __name__ == "__main__":
    main()

