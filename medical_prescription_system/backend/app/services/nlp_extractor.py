import re
from typing import List, Dict, Optional
from transformers import pipeline, AutoTokenizer, AutoModelForTokenClassification
import torch

class NLPDrugExtractor:
    def __init__(self):
        # Initialize NER model for medical entities
        model_name = "d4data/biomedical-ner-all"
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForTokenClassification.from_pretrained(model_name)
            self.ner_pipeline = pipeline("ner", 
                                        model=self.model, 
                                        tokenizer=self.tokenizer,
                                        aggregation_strategy="simple")
        except:
            # Fallback to basic extraction if model loading fails
            self.ner_pipeline = None
        
        # Drug name patterns
        self.drug_patterns = [
            r'\b(?:tab|tablet|cap|capsule|syrup|injection)\s+([A-Za-z]+)\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg)\b',
            r'\b([A-Za-z]+)\s+(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg)\s*(?:tab|tablet|cap|capsule|syrup|injection)\b',
            r'\b([A-Za-z]+)\s*-?\s*(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg)\b'
        ]
        
        # Frequency patterns
        self.frequency_patterns = [
            r'\b(?:once|twice|thrice|\d+\s*times?)\s*(?:daily|a\s*day|per\s*day)\b',
            r'\bq(?:8|12|24)h\b',
            r'\b(?:bid|tid|qid|od)\b',
            r'\bevery\s+(?:\d+\s*hours?|\d+\s*days?)\b'
        ]
    
    def extract_drug_information(self, text: str) -> List[Dict]:
        """Extract drug names, dosages, and frequencies from text"""
        extracted_drugs = []
        
        # Try NER model first
        if self.ner_pipeline:
            try:
                entities = self.ner_pipeline(text)
                for entity in entities:
                    if entity['entity_group'] in ['CHEMICAL', 'DRUG']:
                        drug_info = self._extract_dosage_for_drug(text, entity['word'])
                        if drug_info:
                            extracted_drugs.append(drug_info)
            except Exception as e:
                print(f"NER extraction failed: {e}")
        
        # Fallback to regex patterns
        if not extracted_drugs:
            extracted_drugs = self._regex_extraction(text)
        
        return self._deduplicate_drugs(extracted_drugs)
    
    def _regex_extraction(self, text: str) -> List[Dict]:
        """Extract drugs using regex patterns"""
        drugs = []
        text_lower = text.lower()
        
        for pattern in self.drug_patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                drug_name = match.group(1)
                dosage = match.group(2)
                unit = match.group(3)
                
                # Extract frequency for this drug
                frequency = self._extract_frequency_near_drug(text_lower, match.start(), match.end())
                
                drug_info = {
                    'name': drug_name.capitalize(),
                    'generic_name': drug_name.capitalize(),  # Simplified
                    'dosage_form': self._determine_dosage_form(text_lower, match.start(), match.end()),
                    'strength': f"{dosage} {unit}",
                    'route': 'oral',  # Default assumption
                    'frequency': frequency
                }
                
                drugs.append(drug_info)
        
        return drugs
    
    def _extract_dosage_for_drug(self, text: str, drug_name: str) -> Optional[Dict]:
        """Extract dosage information for a specific drug"""
        # Find the drug in text and look for nearby dosage info
        text_lower = text.lower()
        drug_lower = drug_name.lower()
        
        drug_index = text_lower.find(drug_lower)
        if drug_index == -1:
            return None
        
        # Look in a window around the drug name
        window_start = max(0, drug_index - 50)
        window_end = min(len(text), drug_index + len(drug_name) + 50)
        window_text = text_lower[window_start:window_end]
        
        # Extract dosage
        dosage_pattern = r'(\d+(?:\.\d+)?)\s*(mg|ml|g|mcg)'
        dosage_match = re.search(dosage_pattern, window_text)
        
        if dosage_match:
            dosage = dosage_match.group(1)
            unit = dosage_match.group(2)
            frequency = self._extract_frequency_near_drug(window_text, 0, len(window_text))
            
            return {
                'name': drug_name.capitalize(),
                'generic_name': drug_name.capitalize(),
                'dosage_form': 'tablet',  # Default
                'strength': f"{dosage} {unit}",
                'route': 'oral',
                'frequency': frequency
            }
        
        return None
    
    def _extract_frequency_near_drug(self, text: str, start_pos: int, end_pos: int) -> str:
        """Extract frequency information near a drug mention"""
        # Look in a window around the drug
        window_start = max(0, start_pos - 30)
        window_end = min(len(text), end_pos + 30)
        window_text = text[window_start:window_end]
        
        for pattern in self.frequency_patterns:
            match = re.search(pattern, window_text)
            if match:
                return match.group(0)
        
        return "as directed"  # Default
    
    def _determine_dosage_form(self, text: str, start_pos: int, end_pos: int) -> str:
        """Determine dosage form from context"""
        window_start = max(0, start_pos - 20)
        window_end = min(len(text), end_pos + 20)
        window_text = text[window_start:window_end]
        
        forms = {
            'tablet': ['tab', 'tablet'],
            'capsule': ['cap', 'capsule'],
            'syrup': ['syrup', 'liquid'],
            'injection': ['injection', 'inj']
        }
        
        for form, keywords in forms.items():
            if any(keyword in window_text for keyword in keywords):
                return form
        
        return 'tablet'  # Default
    
    def _deduplicate_drugs(self, drugs: List[Dict]) -> List[Dict]:
        """Remove duplicate drug entries"""
        seen = set()
        unique_drugs = []
        
        for drug in drugs:
            key = (drug['name'].lower(), drug['strength'])
            if key not in seen:
                seen.add(key)
                unique_drugs.append(drug)
        
        return unique_drugs