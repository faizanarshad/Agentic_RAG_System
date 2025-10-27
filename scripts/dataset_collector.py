#!/usr/bin/env python3
"""
Comprehensive Dataset Collection Script for RAG System
Collects data from various public sources with proper attribution and licensing
"""

import os
import requests
import json
import time
from pathlib import Path
from typing import Dict, List, Optional
import logging
from dataclasses import dataclass
from datetime import datetime
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class DataSource:
    """Represents a data source with metadata"""
    name: str
    url: str
    license: str
    content_type: str
    category: str
    description: str
    last_updated: Optional[str] = None
    file_count: int = 0
    total_size: int = 0

class DatasetCollector:
    """Collects and organizes datasets for RAG system"""
    
    def __init__(self, base_dir: str = "datasets"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        self.metadata_file = self.base_dir / "dataset_metadata.json"
        self.sources: List[DataSource] = []
        
    def add_source(self, source: DataSource):
        """Add a data source to the collection"""
        self.sources.append(source)
        logger.info(f"Added source: {source.name}")
    
    def collect_medical_dataset(self):
        """Collect medical knowledge dataset from public sources"""
        logger.info("Starting medical dataset collection...")
        
        medical_dir = self.base_dir / "medical_knowledge"
        medical_dir.mkdir(exist_ok=True)
        
        # Medical data sources
        medical_sources = [
            {
                "name": "CDC Guidelines",
                "category": "clinical_guidelines",
                "urls": [
                    "https://www.cdc.gov/coronavirus/2019-ncov/downloads/community/COVID-19-Community-Guide.pdf",
                    "https://www.cdc.gov/diabetes/pdfs/managing/CDC-Diabetes-Prevention-Program-Guide.pdf",
                    "https://www.cdc.gov/cancer/dcpc/resources/features/cancerscreening/pdf/cancer-screening-guidelines.pdf"
                ],
                "license": "Public Domain",
                "description": "CDC health guidelines and recommendations"
            },
            {
                "name": "WHO Publications",
                "category": "public_health",
                "urls": [
                    "https://apps.who.int/iris/bitstream/handle/10665/44102/9789241597906_eng.pdf",
                    "https://apps.who.int/iris/bitstream/handle/10665/274603/9789241565585-eng.pdf"
                ],
                "license": "CC BY-NC-SA 3.0",
                "description": "World Health Organization guidelines"
            }
        ]
        
        for source_info in medical_sources:
            category_dir = medical_dir / source_info["category"]
            category_dir.mkdir(exist_ok=True)
            
            source = DataSource(
                name=source_info["name"],
                url="",  # Multiple URLs
                license=source_info["license"],
                content_type="PDF",
                category=source_info["category"],
                description=source_info["description"]
            )
            
            for url in source_info["urls"]:
                self._download_file(url, category_dir, source)
            
            self.add_source(source)
    
    def collect_technical_dataset(self):
        """Collect technical documentation dataset"""
        logger.info("Starting technical dataset collection...")
        
        tech_dir = self.base_dir / "technical_docs"
        tech_dir.mkdir(exist_ok=True)
        
        # Technical documentation sources
        tech_sources = [
            {
                "name": "Python Documentation",
                "category": "programming",
                "base_url": "https://docs.python.org/3/",
                "files": [
                    "tutorial/index.html",
                    "library/index.html",
                    "reference/index.html"
                ],
                "license": "PSF License",
                "description": "Official Python documentation"
            },
            {
                "name": "React Documentation",
                "category": "frameworks",
                "base_url": "https://react.dev/",
                "files": [
                    "learn",
                    "reference/react",
                    "reference/react-dom"
                ],
                "license": "MIT License",
                "description": "Official React documentation"
            }
        ]
        
        for source_info in tech_sources:
            category_dir = tech_dir / source_info["category"]
            category_dir.mkdir(exist_ok=True)
            
            source = DataSource(
                name=source_info["name"],
                url=source_info["base_url"],
                license=source_info["license"],
                content_type="HTML/Markdown",
                category=source_info["category"],
                description=source_info["description"]
            )
            
            # Note: For HTML content, you'd need additional parsing
            # This is a placeholder for the structure
            self.add_source(source)
    
    def collect_business_dataset(self):
        """Collect business and compliance dataset"""
        logger.info("Starting business dataset collection...")
        
        business_dir = self.base_dir / "business_compliance"
        business_dir.mkdir(exist_ok=True)
        
        # Business/legal sources (public domain only)
        business_sources = [
            {
                "name": "GDPR Guidelines",
                "category": "compliance",
                "urls": [
                    "https://gdpr.eu/wp-content/uploads/2019/01/Our_Data_Our_Rights_report.pdf"
                ],
                "license": "Public Domain",
                "description": "GDPR compliance guidelines"
            },
            {
                "name": "NIST Cybersecurity Framework",
                "category": "security",
                "urls": [
                    "https://nvlpubs.nist.gov/nistpubs/CSWP/NIST.CSWP.04162018.pdf"
                ],
                "license": "Public Domain",
                "description": "Cybersecurity framework guidelines"
            }
        ]
        
        for source_info in business_sources:
            category_dir = business_dir / source_info["category"]
            category_dir.mkdir(exist_ok=True)
            
            source = DataSource(
                name=source_info["name"],
                url="",
                license=source_info["license"],
                content_type="PDF",
                category=source_info["category"],
                description=source_info["description"]
            )
            
            for url in source_info["urls"]:
                self._download_file(url, category_dir, source)
            
            self.add_source(source)
    
    def collect_educational_dataset(self):
        """Collect educational content dataset"""
        logger.info("Starting educational dataset collection...")
        
        edu_dir = self.base_dir / "educational_content"
        edu_dir.mkdir(exist_ok=True)
        
        # Educational sources (open access)
        edu_sources = [
            {
                "name": "MIT OpenCourseWare",
                "category": "computer_science",
                "description": "MIT open educational resources",
                "license": "CC BY-NC-SA",
                "note": "Would require specific course material URLs"
            },
            {
                "name": "Khan Academy",
                "category": "mathematics",
                "description": "Free educational content",
                "license": "CC BY-NC-SA",
                "note": "Would require API access or specific content URLs"
            }
        ]
        
        # Note: Educational content often requires specific APIs or permissions
        # This is a structure placeholder
        for source_info in edu_sources:
            category_dir = edu_dir / source_info["category"]
            category_dir.mkdir(exist_ok=True)
            
            source = DataSource(
                name=source_info["name"],
                url="",
                license=source_info["license"],
                content_type="Mixed",
                category=source_info["category"],
                description=source_info["description"]
            )
            
            self.add_source(source)
    
    def _download_file(self, url: str, destination_dir: Path, source: DataSource):
        """Download a file from URL with proper error handling"""
        try:
            logger.info(f"Downloading: {url}")
            
            # Create filename from URL
            filename = url.split('/')[-1]
            if not filename.endswith(('.pdf', '.html', '.txt', '.md')):
                filename += '.pdf'  # Default extension
            
            file_path = destination_dir / filename
            
            # Skip if file already exists
            if file_path.exists():
                logger.info(f"File already exists: {filename}")
                return
            
            # Download with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; RAG-Dataset-Collector/1.0)'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Write file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            # Update source metadata
            source.file_count += 1
            source.total_size += len(response.content)
            source.last_updated = datetime.now().isoformat()
            
            logger.info(f"Downloaded: {filename} ({len(response.content)} bytes)")
            
            # Rate limiting
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {str(e)}")
    
    def create_sample_documents(self):
        """Create sample documents for immediate testing"""
        logger.info("Creating sample documents...")
        
        samples_dir = self.base_dir / "samples"
        samples_dir.mkdir(exist_ok=True)
        
        # Sample medical content
        medical_content = """
        # Medical AI and Machine Learning Guide
        
        ## Introduction to Medical AI
        Artificial Intelligence in healthcare is revolutionizing patient care through:
        - Diagnostic imaging analysis
        - Drug discovery acceleration
        - Personalized treatment plans
        - Predictive analytics for patient outcomes
        
        ## Machine Learning in Healthcare
        Common ML applications include:
        1. **Computer Vision**: Medical image analysis, radiology
        2. **Natural Language Processing**: Clinical note analysis
        3. **Predictive Modeling**: Risk assessment, early warning systems
        4. **Recommendation Systems**: Treatment optimization
        
        ## Ethical Considerations
        - Patient privacy and data protection
        - Algorithmic bias and fairness
        - Transparency and explainability
        - Regulatory compliance (FDA, HIPAA)
        
        ## Implementation Guidelines
        - Data quality and validation
        - Clinical workflow integration
        - Continuous monitoring and evaluation
        - Healthcare professional training
        """
        
        # Sample technical content
        tech_content = """
        # RAG Systems Implementation Guide
        
        ## What is RAG?
        Retrieval-Augmented Generation (RAG) combines:
        - Information retrieval from knowledge bases
        - Large language model generation
        - Context-aware response synthesis
        
        ## Architecture Components
        1. **Document Processing**: Text extraction, chunking, preprocessing
        2. **Vector Database**: Embedding storage and similarity search
        3. **Retrieval System**: Query processing and context retrieval
        4. **Generation Model**: LLM for response synthesis
        
        ## Best Practices
        - Chunk size optimization (500-1500 tokens)
        - Embedding model selection
        - Retrieval strategy tuning
        - Response quality evaluation
        
        ## Common Challenges
        - Hallucination mitigation
        - Context window limitations
        - Retrieval relevance
        - Performance optimization
        """
        
        # Sample business content
        business_content = """
        # Data Privacy and Compliance Guide
        
        ## GDPR Compliance
        Key requirements:
        - Lawful basis for processing
        - Data subject rights
        - Privacy by design
        - Data protection impact assessments
        
        ## HIPAA Requirements
        Healthcare data protection:
        - Administrative safeguards
        - Physical safeguards
        - Technical safeguards
        - Business associate agreements
        
        ## Best Practices
        - Regular compliance audits
        - Employee training programs
        - Incident response procedures
        - Documentation and record keeping
        
        ## Risk Management
        - Data classification
        - Access controls
        - Encryption standards
        - Backup and recovery
        """
        
        # Write sample files
        samples = [
            ("medical_ai_guide.txt", medical_content),
            ("rag_implementation.txt", tech_content),
            ("compliance_guide.txt", business_content)
        ]
        
        for filename, content in samples:
            file_path = samples_dir / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Created sample: {filename}")
    
    def save_metadata(self):
        """Save dataset metadata to JSON file"""
        metadata = {
            "collection_date": datetime.now().isoformat(),
            "total_sources": len(self.sources),
            "sources": [
                {
                    "name": source.name,
                    "url": source.url,
                    "license": source.license,
                    "content_type": source.content_type,
                    "category": source.category,
                    "description": source.description,
                    "last_updated": source.last_updated,
                    "file_count": source.file_count,
                    "total_size": source.total_size
                }
                for source in self.sources
            ]
        }
        
        with open(self.metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        logger.info(f"Metadata saved to {self.metadata_file}")
    
    def generate_report(self):
        """Generate a collection report"""
        total_files = sum(source.file_count for source in self.sources)
        total_size = sum(source.total_size for source in self.sources)
        
        report = f"""
# Dataset Collection Report

## Summary
- **Total Sources**: {len(self.sources)}
- **Total Files**: {total_files}
- **Total Size**: {total_size / (1024*1024):.2f} MB
- **Collection Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Sources by Category
"""
        
        categories = {}
        for source in self.sources:
            if source.category not in categories:
                categories[source.category] = []
            categories[source.category].append(source)
        
        for category, sources in categories.items():
            report += f"\n### {category.title()}\n"
            for source in sources:
                report += f"- **{source.name}**: {source.file_count} files, {source.license}\n"
        
        report_file = self.base_dir / "collection_report.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        logger.info(f"Report generated: {report_file}")
        return report

def main():
    """Main execution function"""
    collector = DatasetCollector()
    
    print("🚀 Starting Dataset Collection...")
    print("Choose dataset type:")
    print("1. Medical Knowledge Dataset")
    print("2. Technical Documentation Dataset") 
    print("3. Business & Compliance Dataset")
    print("4. Educational Content Dataset")
    print("5. All Datasets")
    print("6. Sample Documents Only")
    
    choice = input("Enter your choice (1-6): ").strip()
    
    if choice == "1":
        collector.collect_medical_dataset()
    elif choice == "2":
        collector.collect_technical_dataset()
    elif choice == "3":
        collector.collect_business_dataset()
    elif choice == "4":
        collector.collect_educational_dataset()
    elif choice == "5":
        collector.collect_medical_dataset()
        collector.collect_technical_dataset()
        collector.collect_business_dataset()
        collector.collect_educational_dataset()
    elif choice == "6":
        collector.create_sample_documents()
    else:
        print("Invalid choice. Creating sample documents...")
        collector.create_sample_documents()
    
    # Always create samples for immediate testing
    collector.create_sample_documents()
    
    # Save metadata and generate report
    collector.save_metadata()
    report = collector.generate_report()
    
    print("\n" + "="*50)
    print("📊 DATASET COLLECTION COMPLETE!")
    print("="*50)
    print(report)
    print("\n🎯 Next Steps:")
    print("1. Review collected documents in the 'datasets' folder")
    print("2. Upload PDFs to your RAG system via the web interface")
    print("3. Test queries against your new knowledge base")
    print("4. Monitor system performance and adjust as needed")

if __name__ == "__main__":
    main()
