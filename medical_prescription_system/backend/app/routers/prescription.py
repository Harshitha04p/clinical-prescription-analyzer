from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Dict, Any
import logging

from ..models import (PrescriptionRequest, AnalysisResponse, DrugModel, 
                     PatientModel, DrugInteraction, DosageRecommendation, AlternativeDrug)
from ..services.drug_interaction import DrugInteractionDetector
from ..services.dosage_calculator import DosageCalculator
from ..services.alternative_finder import AlternativeFinder
from ..services.nlp_extractor import NLPDrugExtractor

router = APIRouter()

# Initialize services
interaction_detector = DrugInteractionDetector()
dosage_calculator = DosageCalculator()
alternative_finder = AlternativeFinder()
nlp_extractor = NLPDrugExtractor()

@router.post("/analyze-prescription", response_model=AnalysisResponse)
async def analyze_prescription(request: PrescriptionRequest):
    """Analyze a prescription for drug interactions, dosages, and alternatives"""
    try:
        # Extract drugs from raw text if provided
        if request.raw_text and not request.drugs:
            extracted_drugs = nlp_extractor.extract_drug_information(request.raw_text)
            request.drugs = [DrugModel(**drug) for drug in extracted_drugs]
        
        if not request.drugs:
            raise HTTPException(status_code=400, detail="No drugs found in the prescription")
        
        drug_names = [drug.name for drug in request.drugs]
        
        # 1. Detect drug interactions
        interactions = interaction_detector.detect_interactions(drug_names)
        
        # 2. Calculate appropriate dosages
        dosage_recommendations = dosage_calculator.calculate_dosage(request.patient, drug_names)
        
        # 3. Find alternative medications
        interaction_names = [f"{i.drug1}-{i.drug2}" for i in interactions]
        alternatives = alternative_finder.find_alternatives(
            drug_names, request.patient, interaction_names
        )
        
        # 4. Check for contraindications
        warnings = interaction_detector.check_contraindications(
            drug_names, request.patient.medical_conditions
        )
        
        # 5. Calculate overall safety
        risk_score = interaction_detector.calculate_risk_score(interactions)
        is_safe = risk_score < 50  # Threshold for safety
        
        response = AnalysisResponse(
            interactions=interactions,
            dosage_recommendations=dosage_recommendations,
            alternatives=alternatives,
            warnings=warnings,
            is_safe=is_safe
        )
        
        return response
        
    except Exception as e:
        logging.error(f"Error analyzing prescription: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@router.post("/extract-drugs")
async def extract_drugs(text: str):
    """Extract drug information from unstructured text"""
    try:
        extracted_drugs = nlp_extractor.extract_drug_information(text)
        return {"drugs": extracted_drugs}
    except Exception as e:
        logging.error(f"Error extracting drugs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Drug extraction failed: {str(e)}")

@router.get("/drug-info/{drug_name}")
async def get_drug_info(drug_name: str):
    """Get information about a specific drug"""
    
    # This would typically query a comprehensive drug database
    # For demo purposes, return basic structure
    return {
            "name": drug_name,
            "generic_name": drug_name.lower(),
            "therapeutic_class": "Not available"}
    