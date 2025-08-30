from typing import List, Optional
from ..models import DosageRecommendation, AgeGroup, PatientModel
from ..database import drug_db

class DosageCalculator:
    def __init__(self):
        self.age_groups = {
            "pediatric": (0, 12),
            "adolescent": (13, 17),
            "adult": (18, 64),
            "elderly": (65, 120)
        }
    
    def determine_age_group(self, age: int) -> AgeGroup:
        """Determine age group based on patient age"""
        for group_name, (min_age, max_age) in self.age_groups.items():
            if min_age <= age <= max_age:
                return AgeGroup(group_name)
        return AgeGroup.ADULT  # Default fallback
    
    def calculate_dosage(self, patient: PatientModel, drugs: List[str]) -> List[DosageRecommendation]:
        """Calculate appropriate dosages for patient and drugs"""
        recommendations = []
        age_group = self.determine_age_group(patient.age)
        
        for drug in drugs:
            dosage_info = drug_db.get_dosage_recommendation(drug, age_group.value)
            
            if dosage_info:
                # Adjust for weight if pediatric and weight is provided
                min_dose = dosage_info['min_dose']
                max_dose = dosage_info['max_dose']
                
                if age_group == AgeGroup.PEDIATRIC and patient.weight:
                    if dosage_info['unit'] == 'mg/kg':
                        min_dose *= patient.weight
                        max_dose *= patient.weight
                        unit = 'mg'
                    else:
                        unit = dosage_info['unit']
                else:
                    unit = dosage_info['unit']
                
                # Apply elderly dose adjustments
                if age_group == AgeGroup.ELDERLY:
                    min_dose *= 0.75  # Reduce by 25% for elderly
                    max_dose *= 0.75
                
                special_instructions = self._get_special_instructions(
                    drug, age_group, patient.medical_conditions
                )
                
                recommendation = DosageRecommendation(
                    drug_name=drug,
                    age_group=age_group,
                    min_dose=min_dose,
                    max_dose=max_dose,
                    frequency=dosage_info['frequency'],
                    unit=unit,
                    special_instructions=special_instructions
                )
                
                recommendations.append(recommendation)
        
        return recommendations
    
    def _get_special_instructions(self, drug: str, age_group: AgeGroup, 
                                conditions: List[str]) -> Optional[str]:
        """Get special dosing instructions based on patient profile"""
        instructions = []
        
        # Age-specific instructions
        if age_group == AgeGroup.PEDIATRIC:
            instructions.append("Monitor closely for adverse effects")
        elif age_group == AgeGroup.ELDERLY:
            instructions.append("Start with lower dose and titrate slowly")
        
        # Condition-specific adjustments
        condition_adjustments = {
            "renal_disease": "Reduce dose by 50% in renal impairment",
            "hepatic_disease": "Use with caution in liver disease",
            "heart_failure": "Monitor fluid status closely"
        }
        
        for condition in conditions:
            if condition.lower() in condition_adjustments:
                instructions.append(condition_adjustments[condition.lower()])
        
        return "; ".join(instructions) if instructions else None