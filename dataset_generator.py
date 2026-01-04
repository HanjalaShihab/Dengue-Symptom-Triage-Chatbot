import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

class DengueDatasetGenerator:
    def __init__(self, n_samples=2000, seed=42):
        np.random.seed(seed)
        random.seed(seed)
        self.n_samples = n_samples
        
    def generate_synthetic_data(self):
        """Generate realistic dengue patient data"""
        
        data = []
        
        for i in range(self.n_samples):
            # Generate patient profile
            age = self._generate_age()
            gender = random.choice([0, 1])  # 0: Female, 1: Male
            
            # Symptom probabilities based on age and real dengue patterns
            symptom_probs = self._get_symptom_probabilities(age)
            
            # Generate core symptoms (matching your chatbot)
            fever = np.random.binomial(1, symptom_probs['fever'])
            headache = np.random.binomial(1, symptom_probs['headache'])
            eye_pain = np.random.binomial(1, symptom_probs['eye_pain'])
            vomiting = np.random.binomial(1, symptom_probs['vomiting'])
            abdominal_pain = np.random.binomial(1, symptom_probs['abdominal_pain'])
            bleeding = np.random.binomial(1, symptom_probs['bleeding'])
            fatigue = np.random.binomial(1, symptom_probs['fatigue'])
            fluid_accumulation = np.random.binomial(1, symptom_probs['fluid_accumulation'])
            
            # Handle persistent vomiting based on vomiting status
            if vomiting == 1:
                persistent_options = ['none', 'once', 'frequent', 'continuous']
                persistent_weights = [0.1, 0.5, 0.3, 0.1]
                persistent_vomiting = np.random.choice(persistent_options, p=persistent_weights)
            else:
                persistent_vomiting = 'none'
            
            # Additional symptoms for research
            rash = np.random.binomial(1, symptom_probs['rash'])
            joint_pain = np.random.binomial(1, symptom_probs['joint_pain'])
            nausea = np.random.binomial(1, symptom_probs['nausea'])
            diarrhea = np.random.binomial(1, 0.2)
            muscle_pain = np.random.binomial(1, symptom_probs['muscle_pain'])
            
            # Lab values (simulated)
            platelet_count = self._generate_platelet_count(bleeding, fluid_accumulation)
            temperature = self._generate_temperature(fever)
            wbc_count = np.random.normal(4000, 1500)
            
            # Days since onset
            days_since_onset = np.random.randint(1, 8)
            
            # Generate true severity (ground truth)
            true_severity = self._determine_true_severity(
                fever, headache, eye_pain, vomiting, persistent_vomiting,
                abdominal_pain, bleeding, fatigue, fluid_accumulation,
                platelet_count, age
            )
            
            # Generate chatbot predicted severity (using your rules)
            chatbot_severity = self._predict_chatbot_severity(
                fever, headache, eye_pain, vomiting, persistent_vomiting,
                abdominal_pain, bleeding, fatigue, fluid_accumulation
            )
            
            # Risk factors
            previous_dengue = np.random.binomial(1, 0.15)
            comorbidities = np.random.binomial(1, 0.25 if age > 50 else 0.1)
            urban_area = np.random.binomial(1, 0.7)
            
            # Create record
            record = {
                'patient_id': f'P{i+1:04d}',
                'age': age,
                'gender': gender,
                'fever': fever,
                'headache': headache,
                'eye_pain': eye_pain,
                'vomiting': vomiting,
                'persistent_vomiting': persistent_vomiting,
                'abdominal_pain': abdominal_pain,
                'bleeding': bleeding,
                'fatigue': fatigue,
                'fluid_accumulation': fluid_accumulation,
                'rash': rash,
                'joint_pain': joint_pain,
                'nausea': nausea,
                'diarrhea': diarrhea,
                'muscle_pain': muscle_pain,
                'platelet_count': max(10000, platelet_count),
                'temperature': round(temperature, 1),
                'wbc_count': max(1000, wbc_count),
                'days_since_onset': days_since_onset,
                'previous_dengue': previous_dengue,
                'comorbidities': comorbidities,
                'urban_area': urban_area,
                'true_severity': true_severity,
                'chatbot_severity': chatbot_severity,
                'requires_hospitalization': 1 if true_severity in ['Severe', 'Moderate'] else 0,
                'timestamp': (datetime.now() - timedelta(days=random.randint(0, 30))).strftime('%Y-%m-%d')
            }
            
            data.append(record)
        
        return pd.DataFrame(data)
    
    def _generate_age(self):
        """Generate age with dengue-specific distribution"""
        age_groups = ['child', 'adult', 'elderly']
        group = np.random.choice(age_groups, p=[0.3, 0.6, 0.1])
        
        if group == 'child':
            return np.random.randint(1, 18)
        elif group == 'adult':
            return np.random.randint(18, 60)
        else:
            return np.random.randint(60, 85)
    
    def _get_symptom_probabilities(self, age):
        """Get symptom probabilities based on age"""
        if age < 18:  # Children
            return {
                'fever': 0.95, 'headache': 0.6, 'eye_pain': 0.4,
                'vomiting': 0.5, 'abdominal_pain': 0.4, 'bleeding': 0.15,
                'fatigue': 0.7, 'fluid_accumulation': 0.1, 'rash': 0.6,
                'joint_pain': 0.3, 'nausea': 0.4, 'muscle_pain': 0.5
            }
        else:  # Adults
            return {
                'fever': 0.9, 'headache': 0.8, 'eye_pain': 0.6,
                'vomiting': 0.3, 'abdominal_pain': 0.5, 'bleeding': 0.25,
                'fatigue': 0.85, 'fluid_accumulation': 0.2, 'rash': 0.4,
                'joint_pain': 0.7, 'nausea': 0.5, 'muscle_pain': 0.8
            }
    
    def _generate_platelet_count(self, bleeding, fluid_accumulation):
        """Generate platelet count based on severity indicators"""
        base = np.random.normal(200000, 50000)
        
        # Lower platelets for severe symptoms
        if bleeding:
            base *= 0.5
        if fluid_accumulation:
            base *= 0.4
        
        return max(10000, base)
    
    def _generate_temperature(self, fever):
        """Generate temperature based on fever status"""
        if fever:
            return np.random.uniform(38.5, 40.5)
        else:
            return np.random.uniform(36.5, 37.5)
    
    def _determine_true_severity(self, *args):
        """More sophisticated severity determination (ground truth)"""
        # Unpack args
        (fever, headache, eye_pain, vomiting, persistent_vomiting,
         abdominal_pain, bleeding, fatigue, fluid_accumulation,
         platelet_count, age) = args
        
        # Severe criteria (based on WHO guidelines)
        severe_criteria = (
            fluid_accumulation or
            bleeding or
            persistent_vomiting in ['frequent', 'continuous'] or
            platelet_count < 50000 or
            (abdominal_pain and age < 18)  # Warning sign in children
        )
        
        # Moderate criteria
        moderate_criteria = (
            (abdominal_pain and age >= 18) or
            fatigue or
            platelet_count < 100000 or
            persistent_vomiting == 'once'
        )
        
        if severe_criteria and fever:
            return 'Severe'
        elif moderate_criteria and fever:
            return 'Moderate'
        elif fever and not (severe_criteria or moderate_criteria):
            return 'Mild'
        elif fever and not any([headache, eye_pain, vomiting, abdominal_pain, bleeding, fatigue, fluid_accumulation]):
            return 'FeverOnly'
        elif not fever and any([headache, eye_pain, vomiting, abdominal_pain, bleeding, fatigue, fluid_accumulation]):
            return 'OtherSymptoms'
        else:
            return 'NoSymptoms'
    
    def _predict_chatbot_severity(self, *args):
        """Simulate your chatbot's prediction (from rules.py)"""
        (fever, headache, eye_pain, vomiting, persistent_vomiting,
         abdominal_pain, bleeding, fatigue, fluid_accumulation) = args
        
        # Convert to dictionary like in your rules.py
        symptoms = {
            "Fever": fever,
            "Headache": headache,
            "EyePain": eye_pain,
            "Vomiting": vomiting,
            "PersistentVomiting": persistent_vomiting,
            "AbdominalPain": abdominal_pain,
            "Bleeding": bleeding,
            "Fatigue": fatigue,
            "FluidAccumulation": fluid_accumulation
        }
        
        # Your existing logic from rules.py
        has_fever = symptoms.get("Fever") == 1
        warning_signs = (
            symptoms.get("PersistentVomiting") in ["frequent", "continuous"] or
            symptoms.get("AbdominalPain") == 1 or
            symptoms.get("Bleeding") == 1 or
            symptoms.get("Fatigue") == 1 or
            symptoms.get("FluidAccumulation") == 1
        )

        if not any([has_fever, symptoms.get("Headache") == 1, symptoms.get("EyePain") == 1,
                    symptoms.get("Vomiting") == 1, symptoms.get("PersistentVomiting") in ["frequent", "continuous"],
                    symptoms.get("AbdominalPain") == 1, symptoms.get("Bleeding") == 1,
                    symptoms.get("Fatigue") == 1, symptoms.get("FluidAccumulation") == 1]):
            return "NoSymptoms"

        if has_fever and not any([symptoms.get("Headache") == 1, symptoms.get("EyePain") == 1,
                                  symptoms.get("Vomiting") == 1, symptoms.get("PersistentVomiting") in ["frequent", "continuous"],
                                  symptoms.get("AbdominalPain") == 1, symptoms.get("Bleeding") == 1,
                                  symptoms.get("Fatigue") == 1, symptoms.get("FluidAccumulation") == 1]):
            return "FeverOnly"

        if has_fever:
            if warning_signs:
                if symptoms.get("FluidAccumulation") == 1 or symptoms.get("Bleeding") == 1 or symptoms.get("PersistentVomiting") in ["frequent", "continuous"]:
                    return "Severe"
                else:
                    return "Moderate"
            else:
                return "Mild"

        return "OtherSymptoms"
    
    def save_dataset(self, filename='dengue_research_dataset_v1.csv'):
        """Generate and save the dataset"""
        df = self.generate_synthetic_data()
        df.to_csv(filename, index=False)
        print(f"Dataset saved to {filename}")
        print(f"Shape: {df.shape}")
        print(f"Severity distribution:\n{df['true_severity'].value_counts()}")
        return df

# Generate dataset
if __name__ == "__main__":
    generator = DengueDatasetGenerator(n_samples=2000)
    df = generator.save_dataset('dengue_research_dataset_v1.csv')