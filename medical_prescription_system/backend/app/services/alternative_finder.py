from typing import List, Dict
from ..models import AlternativeDrug, PatientModel
from ..database import drug_db

class AlternativeFinder:
    def __init__(self):
        self.therapeutic_equivalents = {
            "aspirin": ["clopidogrel", "ticagrelor"],
            "warfarin": ["rivaroxaban", "apixaban", "dabigatran"],
            "metformin": ["glipizide", "glyburide"],
            "lisinopril": ["losartan", "valsartan"],
            "omeprazole": ["lansoprazole", "pantoprazole"]
        }
        
        self.contraindication_alternatives = {
            "pregnancy": {
                "warfarin": "heparin",
                "ace_inhibitors": "methyldopa",
                "statins": "bile_acid_sequestrants"
            },
            "renal_disease": {
                "metformin": "insulin",
                "nsaids": "acetaminophen"
            }
        }
    
    def find_alternatives(self, drugs: List[str], patient: PatientModel, 
                         interactions: List[str]) -> List[AlternativeDrug]:
        """Find alternative medications based on patient profile and interactions"""
        alternatives = []
        
        for drug in drugs:
            # Check database alternatives
            db_alternatives = drug_db.get_alternatives(drug)
            for alt in db_alternatives:
                alternatives.append(AlternativeDrug(
                    original_drug=drug,
                    alternative_drug=alt['alternative'],
                    reason=alt['reason'],
                    safety_profile=alt['safety_profile']
                ))
            
            # Check therapeutic equivalents
            if drug.lower() in self.therapeutic_equivalents:
                for alt_drug in self.therapeutic_equivalents[drug.lower()]:
                    alternatives.append(AlternativeDrug(
                        original_drug=drug,
                        alternative_drug=alt_drug,
                        reason="Therapeutic equivalent",
                        safety_profile="Similar efficacy with different safety profile"
                    ))
            
            # Check condition-specific alternatives
            for condition in patient.medical_conditions:
                if (condition.lower() in self.contraindication_alternatives and 
                    drug.lower() in self.contraindication_alternatives[condition.lower()]):
                    
                    alt_drug = self.contraindication_alternatives[condition.lower()][drug.lower()]
                    alternatives.append(AlternativeDrug(
                        original_drug=drug,
                        alternative_drug=alt_drug,
                        reason=f"Safer in {condition}",
                        safety_profile=f"Better safety profile for patients with {condition}"
                    ))
        
        return alternatives
    
    def rank_alternatives(self, alternatives: List[AlternativeDrug], 
                         patient: PatientModel) -> List[AlternativeDrug]:
        """Rank alternatives based on patient-specific factors"""
        # Simple ranking based on safety profile keywords
        safety_keywords = ["safer", "better", "reduced risk", "well-tolerated"]
        
        def safety_score(alt: AlternativeDrug) -> int:
            score = 0
            for keyword in safety_keywords:
                if keyword.lower() in alt.safety_profile.lower():
                    score += 1
            return score
        
        return sorted(alternatives, key=safety_score, reverse=True)