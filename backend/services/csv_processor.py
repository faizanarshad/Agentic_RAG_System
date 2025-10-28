"""
CSV File Processing Service for Medical RAG System
Handles CSV datasets with medical data processing capabilities
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
import logging
from datetime import datetime
import json
import re

from core.config import settings
from utils.logger import logger

class CSVProcessor:
    """Process CSV files for medical RAG system"""
    
    def __init__(self):
        self.supported_encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
        self.medical_columns = [
            'diagnosis', 'symptoms', 'treatment', 'medication', 'procedure',
            'condition', 'disease', 'patient_info', 'clinical_notes',
            'medical_history', 'lab_results', 'imaging_results'
        ]
    
    def validate_csv_file(self, file_path: str) -> bool:
        """Validate CSV file format and readability"""
        try:
            # Try to read with different encodings
            for encoding in self.supported_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, nrows=5)
                    if not df.empty:
                        logger.info(f"CSV file validated successfully with encoding: {encoding}")
                        return True
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"Error reading CSV with {encoding}: {str(e)}")
                    continue
            
            logger.error("Could not read CSV file with any supported encoding")
            return False
            
        except Exception as e:
            logger.error(f"Error validating CSV file: {str(e)}")
            return False
    
    def detect_medical_content(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Detect if CSV contains medical content and identify relevant columns"""
        medical_info = {
            'is_medical': False,
            'medical_columns': [],
            'content_type': 'unknown',
            'confidence': 0.0
        }
        
        # Check column names for medical terms
        columns_lower = [col.lower() for col in df.columns]
        medical_score = 0
        
        medical_keywords = [
            'patient', 'diagnosis', 'symptom', 'treatment', 'medication', 'drug',
            'disease', 'condition', 'clinical', 'medical', 'health', 'hospital',
            'doctor', 'physician', 'nurse', 'therapy', 'procedure', 'surgery',
            'lab', 'test', 'result', 'blood', 'pressure', 'heart', 'cancer',
            'diabetes', 'infection', 'pain', 'fever', 'chronic', 'acute'
        ]
        
        for col in columns_lower:
            for keyword in medical_keywords:
                if keyword in col:
                    medical_score += 1
                    medical_info['medical_columns'].append(col)
                    break
        
        # Check content for medical terms (sample first 100 rows)
        sample_df = df.head(100)
        content_score = 0
        
        for col in df.select_dtypes(include=['object']).columns:
            sample_text = ' '.join(sample_df[col].astype(str).values).lower()
            for keyword in medical_keywords:
                if keyword in sample_text:
                    content_score += 1
                    break
        
        total_score = medical_score + content_score
        medical_info['confidence'] = min(total_score / len(df.columns), 1.0)
        medical_info['is_medical'] = medical_info['confidence'] > 0.3
        
        # Determine content type
        if any('diagnosis' in col for col in columns_lower):
            medical_info['content_type'] = 'diagnostic_data'
        elif any('medication' in col or 'drug' in col for col in columns_lower):
            medical_info['content_type'] = 'medication_data'
        elif any('symptom' in col for col in columns_lower):
            medical_info['content_type'] = 'symptom_data'
        elif any('lab' in col or 'test' in col for col in columns_lower):
            medical_info['content_type'] = 'laboratory_data'
        elif medical_info['is_medical']:
            medical_info['content_type'] = 'general_medical'
        
        return medical_info
    
    def anonymize_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove or anonymize potential PHI from CSV data"""
        df_clean = df.copy()
        
        # Columns that might contain PHI
        phi_patterns = [
            r'name', r'id', r'ssn', r'social', r'phone', r'email', r'address',
            r'zip', r'postal', r'birth', r'dob', r'age', r'mrn', r'patient_id'
        ]
        
        columns_to_remove = []
        for col in df_clean.columns:
            col_lower = col.lower()
            for pattern in phi_patterns:
                if re.search(pattern, col_lower):
                    columns_to_remove.append(col)
                    logger.info(f"Removing potential PHI column: {col}")
                    break
        
        # Remove PHI columns
        df_clean = df_clean.drop(columns=columns_to_remove, errors='ignore')
        
        # Anonymize text data that might contain names
        for col in df_clean.select_dtypes(include=['object']).columns:
            if df_clean[col].dtype == 'object':
                # Replace common name patterns with generic terms
                df_clean[col] = df_clean[col].astype(str).str.replace(
                    r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b', 'Patient', regex=True
                )
        
        logger.info(f"Anonymized CSV data: removed {len(columns_to_remove)} potential PHI columns")
        return df_clean
    
    def process_csv_to_documents(self, file_path: str, file_id: str) -> List[Dict[str, Any]]:
        """Process CSV file and convert to document format for RAG"""
        try:
            # Read CSV with best encoding
            df = None
            encoding_used = None
            
            for encoding in self.supported_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                raise Exception("Could not read CSV file with any supported encoding")
            
            logger.info(f"Successfully read CSV with {encoding_used} encoding: {df.shape[0]} rows, {df.shape[1]} columns")
            
            # Detect medical content
            medical_info = self.detect_medical_content(df)
            logger.info(f"Medical content detection: {medical_info}")
            
            # Anonymize data for HIPAA compliance
            df_clean = self.anonymize_data(df)
            
            # Convert to documents
            documents = []
            
            if medical_info['is_medical']:
                documents = self._create_medical_documents(df_clean, file_id, medical_info)
            else:
                documents = self._create_general_documents(df_clean, file_id)
            
            logger.info(f"Created {len(documents)} documents from CSV file")
            return documents
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            raise Exception(f"Failed to process CSV file: {str(e)}")
    
    def _create_medical_documents(self, df: pd.DataFrame, file_id: str, medical_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create medical-specific documents from CSV data"""
        documents = []
        
        # Strategy 1: Row-based documents (each row becomes a document)
        if len(df) <= 1000:  # For smaller datasets
            for idx, row in df.iterrows():
                # Create document text from row
                doc_text = self._format_medical_row(row, medical_info)
                
                if doc_text.strip():
                    doc = {
                        'id': f"{file_id}_row_{idx}",
                        'text': doc_text,
                        'metadata': {
                            'file_id': file_id,
                            'source_type': 'csv',
                            'content_type': medical_info['content_type'],
                            'row_index': int(idx),
                            'is_medical': True,
                            'total_rows': int(len(df)),
                            'chunk_index': int(idx),
                            'total_chunks': int(len(df))
                        }
                    }
                    documents.append(doc)
        
        # Strategy 2: Batch-based documents for larger datasets
        else:  # For larger datasets (create batches of rows)
            batch_size = 10  # Process 10 rows per document for very detailed records
            total_batches = (len(df) + batch_size - 1) // batch_size
            
            for batch_idx in range(total_batches):
                start_idx = batch_idx * batch_size
                end_idx = min(start_idx + batch_size, len(df))
                batch_df = df.iloc[start_idx:end_idx]
                
                # Create document from batch
                doc_text = f"Medical Records Batch {batch_idx + 1} of {total_batches}:\n"
                doc_text += f"Records {start_idx + 1} to {end_idx}:\n\n"
                
                for idx, row in batch_df.iterrows():
                    row_text = self._format_medical_row(row, medical_info)
                    if row_text.strip():
                        doc_text += f"\n{'='*50}\n"
                        doc_text += row_text
                
                if doc_text.strip():
                    doc = {
                        'id': f"{file_id}_batch_{batch_idx}",
                        'text': doc_text,
                        'metadata': {
                            'file_id': file_id,
                            'source_type': 'csv',
                            'content_type': medical_info['content_type'],
                            'batch_index': int(batch_idx),
                            'batch_size': int(len(batch_df)),
                            'is_medical': True,
                            'total_rows': int(len(df)),
                            'chunk_index': int(batch_idx),
                            'total_chunks': int(total_batches)
                        }
                    }
                    documents.append(doc)
            
            logger.info(f"Created {len(documents)} batch documents from {len(df)} rows")
        
        # Strategy 3: Summary document
        summary_doc = self._create_dataset_summary(df, file_id, medical_info)
        documents.append(summary_doc)
        
        return documents
    
    def _format_medical_row(self, row: pd.Series, medical_info: Dict[str, Any]) -> str:
        """Format a single row as medical document text"""
        doc_text = f"Medical Record Entry:\n\n"
        
        # Prioritize medical columns
        medical_cols = medical_info.get('medical_columns', [])
        other_cols = [col for col in row.index if col.lower() not in medical_cols]
        
        # Add medical columns first
        for col in row.index:
            if col.lower() in medical_cols and pd.notna(row[col]):
                value = str(row[col]).strip()
                if value and value.lower() not in ['nan', 'null', '']:
                    doc_text += f"{col.replace('_', ' ').title()}: {value}\n"
        
        # Add other relevant columns
        for col in other_cols:
            if pd.notna(row[col]):
                value = str(row[col]).strip()
                if value and value.lower() not in ['nan', 'null', '']:
                    doc_text += f"{col.replace('_', ' ').title()}: {value}\n"
        
        return doc_text
    
    def _create_general_documents(self, df: pd.DataFrame, file_id: str) -> List[Dict[str, Any]]:
        """Create general documents from non-medical CSV data"""
        documents = []
        
        # Create column-based documents
        for col in df.columns:
            col_data = df[col].dropna().astype(str)
            if len(col_data) > 0:
                # Sample data for large columns
                if len(col_data) > 100:
                    sample_data = col_data.sample(min(50, len(col_data))).tolist()
                    doc_text = f"Data Column - {col.replace('_', ' ').title()}:\n\n"
                    doc_text += f"Sample entries from {len(col_data)} total records:\n"
                    doc_text += "\n".join([f"• {entry}" for entry in sample_data])
                else:
                    doc_text = f"Data Column - {col.replace('_', ' ').title()}:\n\n"
                    doc_text += "\n".join([f"• {entry}" for entry in col_data.tolist()])
                
                doc = {
                    'id': f"{file_id}_column_{col}",
                    'text': doc_text,
                    'metadata': {
                        'file_id': file_id,
                        'source_type': 'csv',
                        'content_type': 'general_data',
                        'column_name': str(col),
                        'is_medical': False,
                        'total_entries': int(len(col_data)),
                        'chunk_index': 0,
                        'total_chunks': 1
                    }
                }
                documents.append(doc)
        
        # Create summary document
        summary_doc = self._create_dataset_summary(df, file_id, {'content_type': 'general_data', 'is_medical': False})
        documents.append(summary_doc)
        
        return documents
    
    def _create_dataset_summary(self, df: pd.DataFrame, file_id: str, medical_info: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary document for the entire dataset"""
        summary_text = f"Dataset Summary:\n\n"
        summary_text += f"Total Records: {len(df)}\n"
        summary_text += f"Total Columns: {len(df.columns)}\n"
        summary_text += f"Content Type: {medical_info.get('content_type', 'unknown')}\n"
        summary_text += f"Medical Content: {'Yes' if medical_info.get('is_medical', False) else 'No'}\n\n"
        
        summary_text += "Column Information:\n"
        for col in df.columns:
            dtype = str(df[col].dtype)
            non_null = df[col].count()
            summary_text += f"• {col.replace('_', ' ').title()}: {dtype}, {non_null} non-null values\n"
        
        # Add data sample
        if len(df) > 0:
            summary_text += f"\nSample Data (first 3 rows):\n"
            for idx, row in df.head(3).iterrows():
                summary_text += f"\nRecord {idx + 1}:\n"
                for col, value in row.items():
                    if pd.notna(value):
                        summary_text += f"  {col}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}\n"
        
        return {
            'id': f"{file_id}_summary",
            'text': summary_text,
            'metadata': {
                'file_id': file_id,
                'source_type': 'csv',
                'content_type': 'dataset_summary',
                'is_medical': medical_info.get('is_medical', False),
                'total_rows': int(len(df)),
                'total_columns': int(len(df.columns)),
                'chunk_index': 0,
                'total_chunks': 1
            }
        }
    
    def get_csv_info(self, file_path: str) -> Dict[str, Any]:
        """Get basic information about CSV file"""
        try:
            # Try to read with different encodings
            df = None
            encoding_used = None
            
            for encoding in self.supported_encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, nrows=10)
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                return {'error': 'Could not read CSV file'}
            
            # Get full dataframe for complete info
            df_full = pd.read_csv(file_path, encoding=encoding_used)
            medical_info = self.detect_medical_content(df_full)
            
            return {
                'rows': len(df_full),
                'columns': len(df_full.columns),
                'column_names': df_full.columns.tolist(),
                'encoding': encoding_used,
                'medical_info': medical_info,
                'file_size_mb': Path(file_path).stat().st_size / (1024 * 1024),
                'estimated_documents': self._estimate_document_count(df_full, medical_info)
            }
            
        except Exception as e:
            logger.error(f"Error getting CSV info: {str(e)}")
            return {'error': str(e)}
    
    def _estimate_document_count(self, df: pd.DataFrame, medical_info: Dict[str, Any]) -> int:
        """Estimate how many documents will be created from CSV"""
        if medical_info.get('is_medical', False):
            if len(df) <= 1000:
                return len(df) + 1  # rows + summary
            else:
                batch_size = 10  # Updated to match new batch size
                total_batches = (len(df) + batch_size - 1) // batch_size
                return total_batches + 1  # batches + summary
        else:
            return len(df.columns) + 1  # columns + summary
