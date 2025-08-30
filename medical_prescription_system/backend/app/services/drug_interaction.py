from typing import List, Dict
from ..models import DrugInteraction, SeverityLevel
from ..database import drug_db
import re

class DrugInteractionDetector:
    def __init__(self):
        self.severity_weights = {
            "mild": 1,
            "moderate": 2,
            "severe": 3,
            "contraindicated": 4
        }
    
    def detect_interactions(self, drugs: List[str]) -> List[DrugInteraction]:
        """Detect drug interactions for given list of drugs"""
        interactions = []
        raw_interactions = drug_db.get_drug_interactions(drugs)
        
        for interaction in raw_interactions:
            interactions.append(DrugInteraction(
                drug1=interaction['drug1'],
                drug2=interaction['drug2'],
                severity=SeverityLevel(interaction['severity']),
                description=interaction['description'],
                mechanism=interaction['mechanism'],
                management=interaction['management']
            ))
        
        # Sort by severity (most severe first)
        interactions.sort(key=lambda x: self.severity_weights[x.severity.value], reverse=True)
        
        return interactions
    
    def check_contraindications(self, drugs: List[str], medical_conditions: List[str]) -> List[str]:
        """Check for drug contraindications based on medical conditions"""
        warnings = []
        
        contraindication_rules = {
            "warfarin": ["active_bleeding", "pregnancy"],
            "metformin": ["renal_failure", "heart_failure"],
            "nsaids": ["peptic_ulcer", "renal_disease"],
            "ace_inhibitors": ["pregnancy", "hyperkalemia"]
        }
        
        for drug in drugs:
            drug_lower = drug.lower()
            if drug_lower in contraindication_rules:
                for condition in medical_conditions:
                    if condition.lower() in contraindication_rules[drug_lower]:
                        warnings.append(f"{drug} is contraindicated in {condition}")
        
        return warnings
    
    def calculate_risk_score(self, interactions: List[DrugInteraction]) -> float:
        """Calculate overall risk score based on interactions"""
        if not interactions:
            return 0.0
        
        total_score = sum(self.severity_weights[interaction.severity.value] 
                         for interaction in interactions)
        max_possible = len(interactions) * 4  # 4 is max severity weight
        
        return (total_score / max_possible) * 100 if max_possible > 0 else 0.0