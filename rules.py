# rules.py - WHO Dengue Classification Rules

def determine_severity(symptoms):
    """
    Determine dengue severity based on WHO guidelines:
    
    WHO Classification:
    1. Dengue without warning signs (fever + 2 of: nausea/vomiting, rash, aches, positive tourniquet test)
    2. Dengue with warning signs (fever + any warning sign)
    3. Severe dengue (fever + severe plasma leakage, severe bleeding, severe organ impairment)
    
    For our simplified version:
    - FeverOnly: Just fever without other symptoms
    - Mild: Fever + 1-2 other symptoms (no warning signs)
    - Moderate: Fever + warning signs but no severe symptoms
    - Severe: Fever + severe symptoms (bleeding, fluid accumulation, etc.)
    """
    
    # Convert symptoms to our format if needed
    if isinstance(symptoms, dict):
        fever = symptoms.get("Fever") == 1
        headache = symptoms.get("Headache") == 1
        eye_pain = symptoms.get("EyePain") == 1
        vomiting = symptoms.get("Vomiting") == 1
        persistent_vomiting = symptoms.get("PersistentVomiting")
        abdominal_pain = symptoms.get("AbdominalPain") == 1
        bleeding = symptoms.get("Bleeding") == 1
        fatigue = symptoms.get("Fatigue") == 1
        fluid_accumulation = symptoms.get("FluidAccumulation") == 1
    else:
        # Assume symptoms is a tuple/list
        fever, headache, eye_pain, vomiting, persistent_vomiting, abdominal_pain, bleeding, fatigue, fluid_accumulation = symptoms

    # Count symptoms (excluding fever)
    other_symptoms = [headache, eye_pain, vomiting, abdominal_pain, fatigue]
    other_symptom_count = sum(other_symptoms)
    
    # WHO Warning Signs (according to simplified version)
    warning_signs = (
        abdominal_pain or
        persistent_vomiting in ["frequent", "continuous"] or
        bleeding or
        fatigue or
        fluid_accumulation
    )
    
    # WHO Severe Criteria
    severe_criteria = (
        fluid_accumulation or
        bleeding or
        persistent_vomiting in ["frequent", "continuous"] or
        (abdominal_pain and vomiting)  # Severe abdominal pain with vomiting
    )
    
    # Apply WHO Classification Logic
    if not fever and not any([headache, eye_pain, vomiting, abdominal_pain, bleeding, fatigue, fluid_accumulation]):
        return "NoSymptoms"
    
    elif fever and not any([headache, eye_pain, vomiting, abdominal_pain, bleeding, fatigue, fluid_accumulation]):
        # WHO: Dengue without warning signs (mild case)
        return "Mild"
    
    elif not fever and any([headache, eye_pain, vomiting, abdominal_pain, bleeding, fatigue, fluid_accumulation]):
        return "OtherSymptoms"
    
    elif fever:
        if severe_criteria:
            # WHO: Severe Dengue
            return "Severe"
        elif warning_signs:
            # WHO: Dengue with warning signs
            return "Moderate"
        else:
            # WHO: Dengue without warning signs (but has some symptoms)
            return "Mild"
    
    else:
        return "NoSymptoms"


# Test function to verify logic
def test_rules():
    """Test the rule-based system with various scenarios"""
    
    test_cases = [
        {
            "name": "Fever only",
            "symptoms": {"Fever": 1, "Headache": 0, "EyePain": 0, "Vomiting": 0, 
                        "PersistentVomiting": "none", "AbdominalPain": 0, 
                        "Bleeding": 0, "Fatigue": 0, "FluidAccumulation": 0},
            "expected": "Mild"  # WHO: Dengue without warning signs
        },
        {
            "name": "Fever + headache",
            "symptoms": {"Fever": 1, "Headache": 1, "EyePain": 0, "Vomiting": 0,
                        "PersistentVomiting": "none", "AbdominalPain": 0,
                        "Bleeding": 0, "Fatigue": 0, "FluidAccumulation": 0},
            "expected": "Mild"  # WHO: Dengue without warning signs
        },
        {
            "name": "Fever + abdominal pain (warning sign)",
            "symptoms": {"Fever": 1, "Headache": 0, "EyePain": 0, "Vomiting": 0,
                        "PersistentVomiting": "none", "AbdominalPain": 1,
                        "Bleeding": 0, "Fatigue": 0, "FluidAccumulation": 0},
            "expected": "Moderate"  # WHO: Dengue with warning signs
        },
        {
            "name": "Fever + fluid accumulation (severe)",
            "symptoms": {"Fever": 1, "Headache": 0, "EyePain": 0, "Vomiting": 0,
                        "PersistentVomiting": "none", "AbdominalPain": 0,
                        "Bleeding": 0, "Fatigue": 0, "FluidAccumulation": 1},
            "expected": "Severe"  # WHO: Severe dengue
        },
        {
            "name": "No symptoms",
            "symptoms": {"Fever": 0, "Headache": 0, "EyePain": 0, "Vomiting": 0,
                        "PersistentVomiting": "none", "AbdominalPain": 0,
                        "Bleeding": 0, "Fatigue": 0, "FluidAccumulation": 0},
            "expected": "NoSymptoms"
        },
        {
            "name": "Headache only (no fever)",
            "symptoms": {"Fever": 0, "Headache": 1, "EyePain": 0, "Vomiting": 0,
                        "PersistentVomiting": "none", "AbdominalPain": 0,
                        "Bleeding": 0, "Fatigue": 0, "FluidAccumulation": 0},
            "expected": "OtherSymptoms"
        },
    ]
    
    print("Testing WHO Dengue Classification Rules:")
    print("=" * 60)
    
    all_passed = True
    for test in test_cases:
        result = determine_severity(test["symptoms"])
        passed = result == test["expected"]
        all_passed = all_passed and passed
        
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} {test['name']}")
        print(f"  Expected: {test['expected']}, Got: {result}")
        if not passed:
            print(f"  Symptoms: {test['symptoms']}")
        print()
    
    if all_passed:
        print("✅ All tests passed! WHO classification logic is correct.")
    else:
        print("❌ Some tests failed. Please check the logic.")
    
    return all_passed


if __name__ == "__main__":
    test_rules()