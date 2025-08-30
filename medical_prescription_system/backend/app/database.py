import pandas as pd
import json
from pathlib import Path
from typing import List, Dict, Any

class DrugDatabase:
    def __init__(self):
        self.data_path = Path("data")
        self.interactions_df = None
        self.dosages_df = None
        self.alternatives_df = None
        self.load_data()
    
    def load_data(self):
        """Load drug data from CSV files"""
        try:
            # Load drug interactions
            interactions_data = [
                {"drug1": "warfarin", "drug2": "aspirin", "severity": "severe", 
                 "description": "Increased bleeding risk", 
                 "mechanism": "Additive anticoagulant effects",
                 "management": "Monitor INR closely, consider dose reduction"},
                {"drug1": "metformin", "drug2": "contrast_dye", "severity": "moderate",
                 "description": "Risk of lactic acidosis",
                 "mechanism": "Impaired renal function",
                 "management": "Discontinue metformin 48h before contrast"},
                {"drug1": "digoxin", "drug2": "quinidine", "severity": "severe",
                 "description": "Digoxin toxicity",
                 "mechanism": "Quinidine inhibits P-glycoprotein",
                 "management": "Reduce digoxin dose by 50%"},
            ]
            self.interactions_df = pd.DataFrame(interactions_data)
            
            # Load dosage recommendations
            dosage_data = [
                {"drug": "paracetamol", "age_group": "pediatric", "min_dose": 10, 
                 "max_dose": 15, "frequency": "q6h", "unit": "mg/kg"},
                {"drug": "paracetamol", "age_group": "adult", "min_dose": 500, 
                 "max_dose": 1000, "frequency": "q6h", "unit": "mg"},
                {"drug": "ibuprofen", "age_group": "pediatric", "min_dose": 5, 
                 "max_dose": 10, "frequency": "q8h", "unit": "mg/kg"},
                {"drug": "ibuprofen", "age_group": "adult", "min_dose": 400, 
                 "max_dose": 800, "frequency": "q8h", "unit": "mg"},
            ]
            self.dosages_df = pd.DataFrame(dosage_data)
            
            # Load alternative medications
            alternatives_data = [
                {"original": "aspirin", "alternative": "clopidogrel", 
                 "reason": "GI intolerance", "safety_profile": "Better GI tolerance"},
                {"original": "warfarin", "alternative": "rivaroxaban", 
                 "reason": "Monitoring burden", "safety_profile": "No routine monitoring required"},
            ]
            self.alternatives_df = pd.DataFrame(alternatives_data)
            
        except Exception as e:
            print(f"Error loading data: {e}")
            # Initialize with empty DataFrames if files don't exist
            self.interactions_df = pd.DataFrame()
            self.dosages_df = pd.DataFrame()
            self.alternatives_df = pd.DataFrame()
    
    def get_drug_interactions(self, drugs: List[str]) -> List[Dict]:
        """Get interactions between provided drugs"""
        interactions = []
        if self.interactions_df.empty:
            return interactions
            
        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i+1:]:
                # Check both directions
                interaction = self.interactions_df[
                    ((self.interactions_df['drug1'] == drug1.lower()) & 
                     (self.interactions_df['drug2'] == drug2.lower())) |
                    ((self.interactions_df['drug1'] == drug2.lower()) & 
                     (self.interactions_df['drug2'] == drug1.lower()))
                ]
                if not interaction.empty:
                    interactions.extend(interaction.to_dict('records'))
        
        return interactions
    
    def get_dosage_recommendation(self, drug: str, age_group: str) -> Dict:
        """Get dosage recommendation for specific drug and age group"""
        if self.dosages_df.empty:
            return {}
            
        dosage = self.dosages_df[
            (self.dosages_df['drug'] == drug.lower()) & 
            (self.dosages_df['age_group'] == age_group)
        ]
        
        if not dosage.empty:
            return dosage.iloc[0].to_dict()
        return {}
    
    def get_alternatives(self, drug: str) -> List[Dict]:
        """Get alternative medications for a drug"""
        if self.alternatives_df.empty:
            return []
            
        alternatives = self.alternatives_df[
            self.alternatives_df['original'] == drug.lower()
        ]
        
        return alternatives.to_dict('records')

# Global database instance
drug_db = DrugDatabase()