from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class AgeGroup(str, Enum):
    PEDIATRIC = "pediatric"  # 0-12 years
    ADOLESCENT = "adolescent"  # 13-17 years
    ADULT = "adult"  # 18-64 years
    ELDERLY = "elderly"  # 65+ years

class SeverityLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CONTRAINDICATED = "contraindicated"

class DrugModel(BaseModel):
    name: str
    generic_name: str
    dosage_form: str  # tablet, capsule, liquid, etc.
    strength: str  # mg, ml, etc.
    route: str  # oral, IV, topical, etc.

class PatientModel(BaseModel):
    age: int
    weight: Optional[float] = None
    medical_conditions: List[str] = []
    allergies: List[str] = []

class PrescriptionRequest(BaseModel):
    patient: PatientModel
    drugs: List[DrugModel]
    raw_text: Optional[str] = None

class DrugInteraction(BaseModel):
    drug1: str
    drug2: str
    severity: SeverityLevel
    description: str
    mechanism: str
    management: str

class DosageRecommendation(BaseModel):
    drug_name: str
    age_group: AgeGroup
    min_dose: float
    max_dose: float
    frequency: str
    unit: str
    special_instructions: Optional[str] = None

class AlternativeDrug(BaseModel):
    original_drug: str
    alternative_drug: str
    reason: str
    safety_profile: str

class AnalysisResponse(BaseModel):
    interactions: List[DrugInteraction]
    dosage_recommendations: List[DosageRecommendation]
    alternatives: List[AlternativeDrug]
    warnings: List[str]
    is_safe: bool