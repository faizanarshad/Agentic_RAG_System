"""
Medical RAG System Configuration
Specialized settings for medical use cases with HIPAA compliance
"""

import os
from typing import List, Dict, Any
from datetime import datetime

class MedicalRAGConfig:
    """Medical-specific configuration for RAG system"""
    
    # Medical specialties supported
    MEDICAL_SPECIALTIES = [
        "cardiology",
        "radiology", 
        "oncology",
        "emergency_medicine",
        "pharmacology",
        "clinical_guidelines",
        "medical_terminology",
        "diagnostic_procedures"
    ]
    
    # Medical-specific prompts
    MEDICAL_SYSTEM_PROMPT = """
You are a medical AI assistant designed to provide evidence-based information from peer-reviewed medical literature and clinical guidelines. 

IMPORTANT DISCLAIMERS:
- This system is for educational and informational purposes only
- Do not provide specific medical advice, diagnosis, or treatment recommendations
- Always recommend consulting qualified healthcare professionals for medical decisions
- Responses should be based on established medical knowledge and guidelines

When responding to medical queries:
1. Provide accurate, evidence-based information
2. Include relevant medical terminology with explanations
3. Cite sources when possible
4. Emphasize the importance of professional medical consultation
5. Use appropriate medical formatting and structure

Remember: You are a tool to support medical education and information access, not a replacement for professional medical judgment.
"""
    
    # Medical query examples
    MEDICAL_SAMPLE_QUESTIONS = [
        "What are the symptoms and treatment options for myocardial infarction?",
        "Explain the mechanism of action of ACE inhibitors in hypertension",
        "What are the diagnostic criteria for sepsis?",
        "Describe the stages of chronic kidney disease",
        "What are the contraindications for MRI imaging?",
        "Explain the pathophysiology of Type 2 diabetes",
        "What are the side effects of chemotherapy?",
        "Describe the emergency management of anaphylaxis"
    ]
    
    # HIPAA compliance settings
    HIPAA_COMPLIANCE = {
        "phi_handling": "anonymized",
        "audit_logging": True,
        "access_controls": True,
        "data_encryption": True,
        "retention_policy": "7_years",
        "user_authentication": True
    }
    
    # Medical terminology support
    MEDICAL_TERMINOLOGY = {
        "abbreviation_expansion": True,
        "medical_spell_check": True,
        "drug_name_recognition": True,
        "anatomy_references": True,
        "icd_code_support": True,
        "cpt_code_support": True
    }
    
    # Clinical decision support features
    CLINICAL_FEATURES = {
        "drug_interaction_checking": True,
        "dosage_calculations": True,
        "lab_value_interpretation": True,
        "diagnostic_support": True,
        "treatment_guidelines": True,
        "evidence_grading": True
    }
    
    @classmethod
    def get_medical_prompt_template(cls) -> str:
        """Get medical-specific prompt template"""
        return f"""
{cls.MEDICAL_SYSTEM_PROMPT}

Context from medical literature:
{{context}}

Medical Query: {{query}}

Please provide an evidence-based response following medical standards and include appropriate disclaimers.
"""
    
    @classmethod
    def get_medical_metadata(cls) -> Dict[str, Any]:
        """Get medical system metadata"""
        return {
            "system_type": "medical_rag",
            "version": "1.0.0",
            "specialties": cls.MEDICAL_SPECIALTIES,
            "compliance": cls.HIPAA_COMPLIANCE,
            "features": {
                **cls.MEDICAL_TERMINOLOGY,
                **cls.CLINICAL_FEATURES
            },
            "last_updated": datetime.now().isoformat(),
            "disclaimer": "For educational purposes only. Not for clinical decision making."
        }
    
    @classmethod
    def validate_medical_query(cls, query: str) -> Dict[str, Any]:
        """Validate and categorize medical queries"""
        query_lower = query.lower()
        
        # Check for emergency keywords
        emergency_keywords = [
            "emergency", "urgent", "critical", "life-threatening",
            "cardiac arrest", "stroke", "heart attack", "overdose",
            "severe bleeding", "anaphylaxis", "respiratory failure"
        ]
        
        is_emergency = any(keyword in query_lower for keyword in emergency_keywords)
        
        # Detect specialty
        specialty = "general"
        for spec in cls.MEDICAL_SPECIALTIES:
            if spec.replace("_", " ") in query_lower:
                specialty = spec
                break
        
        # Check for drug-related queries
        drug_keywords = ["medication", "drug", "prescription", "dosage", "side effects"]
        is_drug_related = any(keyword in query_lower for keyword in drug_keywords)
        
        return {
            "is_emergency": is_emergency,
            "specialty": specialty,
            "is_drug_related": is_drug_related,
            "requires_disclaimer": True,
            "complexity": "high" if is_emergency else "medium"
        }

# Medical response templates
MEDICAL_RESPONSE_TEMPLATES = {
    "emergency_disclaimer": """
⚠️ MEDICAL EMERGENCY DISCLAIMER ⚠️
If this is a medical emergency, please call 911 or go to the nearest emergency room immediately. 
This AI system cannot provide emergency medical care or replace immediate professional medical attention.
""",
    
    "general_disclaimer": """
📋 Medical Disclaimer: This information is for educational purposes only and should not replace professional medical advice. Always consult with qualified healthcare providers for medical decisions.
""",
    
    "drug_disclaimer": """
💊 Medication Disclaimer: Drug information provided is for educational purposes only. Always consult with a pharmacist or physician before starting, stopping, or changing medications.
""",
    
    "source_attribution": """
📚 Sources: Information based on peer-reviewed medical literature and established clinical guidelines.
"""
}

# Medical file processing settings
MEDICAL_FILE_SETTINGS = {
    "allowed_extensions": [".pdf", ".txt", ".docx"],
    "max_file_size": 50 * 1024 * 1024,  # 50MB
    "chunk_size": 1000,  # Optimal for medical content
    "chunk_overlap": 200,
    "medical_terminology_preservation": True,
    "citation_extraction": True
}

