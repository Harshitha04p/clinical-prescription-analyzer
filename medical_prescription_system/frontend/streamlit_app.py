import streamlit as st
import requests
import json
import pandas as pd
from typing import Dict, List

# Configure page
st.set_page_config(
    page_title="AI Medical Prescription Verification",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:8000/api/v1"

def init_session_state():
    """Initialize session state variables"""
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = {}

def create_patient_sidebar():
    """Create patient information sidebar"""
    st.sidebar.header("👤 Patient Information")
    
    age = st.sidebar.number_input("Age", min_value=0, max_value=120, value=30)
    weight = st.sidebar.number_input("Weight (kg)", min_value=0.0, max_value=300.0, 
                                   value=70.0, step=0.1)
    
    st.sidebar.subheader("Medical Conditions")
    conditions = st.sidebar.multiselect(
        "Select applicable conditions:",
        ["diabetes", "hypertension", "renal_disease", "hepatic_disease", 
         "heart_failure", "pregnancy", "peptic_ulcer"]
    )
    
    st.sidebar.subheader("Known Allergies")
    allergies = st.sidebar.text_area("Enter allergies (one per line)")
    allergy_list = [allergy.strip() for allergy in allergies.split('\n') if allergy.strip()]
    
    return {
        "age": age,
        "weight": weight,
        "medical_conditions": conditions,
        "allergies": allergy_list
    }

def analyze_prescription(patient_data: Dict, drugs: List[Dict], raw_text: str = None):
    """Send prescription for analysis"""
    try:
        payload = {
            "patient": patient_data,
            "drugs": drugs,
            "raw_text": raw_text
        }
        
        response = requests.post(f"{API_BASE_URL}/analyze-prescription", 
                               json=payload)
        
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return None

def extract_drugs_from_text(text: str):
    """Extract drugs from unstructured text"""
    try:
        response = requests.post(f"{API_BASE_URL}/extract-drugs", 
                               params={"text": text})
        
        if response.status_code == 200:
            return response.json().get("drugs", [])
        else:
            st.error(f"Extraction Error: {response.status_code}")
            return []
            
    except requests.exceptions.RequestException as e:
        st.error(f"Connection Error: {str(e)}")
        return []

def display_interactions(interactions: List[Dict]):
    """Display drug interactions"""
    if not interactions:
        st.success("✅ No significant drug interactions detected")
        return
    
    st.subheader("⚠️ Drug Interactions Detected")
    
    for interaction in interactions:
        severity = interaction['severity']
        
        # Color coding based on severity
        if severity == 'severe':
            st.error(f"🚨 **SEVERE**: {interaction['drug1'].title()} ↔️ {interaction['drug2'].title()}")
        elif severity == 'moderate':
            st.warning(f"⚠️ **MODERATE**: {interaction['drug1'].title()} ↔️ {interaction['drug2'].title()}")
        else:
            st.info(f"ℹ️ **MILD**: {interaction['drug1'].title()} ↔️ {interaction['drug2'].title()}")
        
        with st.expander(f"Details: {interaction['drug1'].title()} + {interaction['drug2'].title()}"):
            st.write(f"**Description:** {interaction['description']}")
            st.write(f"**Mechanism:** {interaction['mechanism']}")
            st.write(f"**Management:** {interaction['management']}")

def display_dosage_recommendations(recommendations: List[Dict]):
    """Display dosage recommendations"""
    if not recommendations:
        st.info("No specific dosage recommendations available")
        return
    
    st.subheader("💊 Dosage Recommendations")
    
    for rec in recommendations:
        with st.expander(f"{rec['drug_name'].title()} - {rec['age_group'].title()} Patient"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Minimum Dose", f"{rec['min_dose']:.1f} {rec['unit']}")
                st.write(f"**Frequency:** {rec['frequency']}")
            
            with col2:
                st.metric("Maximum Dose", f"{rec['max_dose']:.1f} {rec['unit']}")
                if rec.get('special_instructions'):
                    st.write(f"**Special Instructions:** {rec['special_instructions']}")

def display_alternatives(alternatives: List[Dict]):
    """Display alternative medications"""
    if not alternatives:
        st.info("No alternative medications suggested")
        return
    
    st.subheader("🔄 Alternative Medications")
    
    df_data = []
    for alt in alternatives:
        df_data.append({
            "Original Drug": alt['original_drug'].title(),
            "Alternative": alt['alternative_drug'].title(),
            "Reason": alt['reason'],
            "Safety Profile": alt['safety_profile']
        })
    
    df = pd.DataFrame(df_data)
    st.dataframe(df, use_container_width=True)

def main():
    """Main Streamlit application"""
    init_session_state()
    
    # Header
    st.title("🏥 AI Medical Prescription Verification System")
    st.markdown("---")
    
    # Patient information sidebar
    patient_data = create_patient_sidebar()
    st.session_state.patient_data = patient_data
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("📝 Prescription Input")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Manual Drug Entry", "Text Extraction"]
        )
        
        drugs = []
        raw_text = None
        
        if input_method == "Manual Drug Entry":
            st.subheader("Add Medications")
            
            # Drug entry form
            with st.form("drug_form"):
                col_name, col_dose, col_form = st.columns(3)
                
                with col_name:
                    drug_name = st.text_input("Drug Name")
                with col_dose:
                    strength = st.text_input("Strength (e.g., 500 mg)")
                with col_form:
                    dosage_form = st.selectbox("Form", 
                                             ["tablet", "capsule", "syrup", "injection"])
                
                route = st.selectbox("Route", ["oral", "IV", "IM", "topical"])
                
                if st.form_submit_button("Add Drug"):
                    if drug_name and strength:
                        drug = {
                            "name": drug_name,
                            "generic_name": drug_name,
                            "dosage_form": dosage_form,
                            "strength": strength,
                            "route": route
                        }
                        
                        if 'current_drugs' not in st.session_state:
                            st.session_state.current_drugs = []
                        st.session_state.current_drugs.append(drug)
                        st.success(f"Added {drug_name}")
                        st.rerun()
            
            # Display current drugs
            if 'current_drugs' in st.session_state and st.session_state.current_drugs:
                st.subheader("Current Prescription")
                for i, drug in enumerate(st.session_state.current_drugs):
                    col_drug, col_remove = st.columns([4, 1])
                    with col_drug:
                        st.write(f"**{drug['name']}** - {drug['strength']} ({drug['dosage_form']})")
                    with col_remove:
                        if st.button("Remove", key=f"remove_{i}"):
                            st.session_state.current_drugs.pop(i)
                            st.rerun()
                
                drugs = st.session_state.current_drugs
        
        else:  # Text Extraction
            st.subheader("Enter Prescription Text")
            raw_text = st.text_area(
                "Paste prescription text here:",
                height=200,
                placeholder="e.g., Paracetamol 500mg tablet twice daily, Ibuprofen 400mg capsule thrice daily..."
            )
            
            if st.button("Extract Drugs") and raw_text:
                with st.spinner("Extracting drug information..."):
                    extracted_drugs = extract_drugs_from_text(raw_text)
                    if extracted_drugs:
                        st.success(f"Extracted {len(extracted_drugs)} medications")
                        drugs = extracted_drugs
                        
                        # Display extracted drugs
                        st.subheader("Extracted Medications")
                        for drug in extracted_drugs:
                            st.write(f"- **{drug['name']}** ({drug['strength']}) - {drug.get('frequency', 'as directed')}")
    
    with col2:
        st.header("🔍 Quick Analysis")
        
        if st.button("🚀 Analyze Prescription", type="primary", use_container_width=True):
            if not drugs:
                st.error("Please add medications to analyze")
            else:
                with st.spinner("Analyzing prescription..."):
                    # Prepare request
                    request_data = {
                        "patient": patient_data,
                        "drugs": drugs,
                        "raw_text": raw_text
                    }
                    
                    # Get analysis
                    results = analyze_prescription(patient_data, drugs, raw_text)
                    
                    if results:
                        st.session_state.analysis_results = results
                        st.success("Analysis completed!")
                        st.rerun()
        
        # Display patient summary
        st.subheader("👤 Patient Summary")
        st.write(f"**Age:** {patient_data['age']} years")
        st.write(f"**Weight:** {patient_data['weight']} kg")
        if patient_data['medical_conditions']:
            st.write(f"**Conditions:** {', '.join(patient_data['medical_conditions'])}")
        if patient_data['allergies']:
            st.write(f"**Allergies:** {', '.join(patient_data['allergies'])}")
    
    # Display results
    if st.session_state.analysis_results:
        st.markdown("---")
        st.header("📊 Analysis Results")
        
        results = st.session_state.analysis_results
        
        # Safety indicator
        if results['is_safe']:
            st.success("✅ Prescription appears to be safe overall")
        else:
            st.error("❌ Prescription has significant safety concerns")
        
        # Create tabs for different sections
        tab1, tab2, tab3, tab4 = st.tabs([
            "🔄 Interactions", 
            "💊 Dosages", 
            "🔄 Alternatives", 
            "⚠️ Warnings"
        ])
        
        with tab1:
            display_interactions(results.get('interactions', []))
        
        with tab2:
            display_dosage_recommendations(results.get('dosage_recommendations', []))
        
        with tab3:
            display_alternatives(results.get('alternatives', []))
        
        with tab4:
            warnings = results.get('warnings', [])
            if warnings:
                for warning in warnings:
                    st.warning(f"⚠️ {warning}")
            else:
                st.success("No specific warnings for this patient profile")
        
        # Export functionality
        st.subheader("📥 Export Results")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Download JSON Report"):
                report = json.dumps(results, indent=2)
                st.download_button(
                    label="Download JSON",
                    data=report,
                    file_name="prescription_analysis.json",
                    mime="application/json"
                )
        
        with col2:
            if st.button("Generate PDF Report"):
                st.info("PDF generation feature coming soon!")

if __name__ == "__main__":
    main()