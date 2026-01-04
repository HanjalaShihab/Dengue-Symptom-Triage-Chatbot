import joblib
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import cross_val_score
import warnings
warnings.filterwarnings('ignore')

class DengueMLPredictor:
    def __init__(self, model_path='dengue_model.pkl', encoder_path='label_encoder.pkl'):
        self.model_path = model_path
        self.encoder_path = encoder_path
        self.model_version = '1.0'
        self.model = None
        self.label_encoder = None
        self.feature_names = [
            'fever', 'headache', 'eye_pain', 'vomiting', 
            'persistent_vomiting_encoded', 'abdominal_pain', 
            'bleeding', 'fatigue', 'fluid_accumulation'
        ]
        self.symptom_map = {
            "Fever": "fever",
            "Headache": "headache", 
            "EyePain": "eye_pain",
            "Vomiting": "vomiting",
            "PersistentVomiting": "persistent_vomiting_encoded",
            "AbdominalPain": "abdominal_pain",
            "Bleeding": "bleeding",
            "Fatigue": "fatigue",
            "FluidAccumulation": "fluid_accumulation"
        }
        
    def prepare_training_data(self, dataset_path='dengue_research_dataset_v1.csv'):
        """Prepare data for training"""
        df = pd.read_csv(dataset_path)
        
        # Encode persistent vomiting
        vomiting_map = {'none': 0, 'once': 1, 'frequent': 2, 'continuous': 3}
        df['persistent_vomiting_encoded'] = df['persistent_vomiting'].map(vomiting_map)
        
        # Prepare features (X) and target (y)
        X = df[self.feature_names].fillna(0)
        
        # Encode severity labels
        self.label_encoder = LabelEncoder()
        severity_order = ['NoSymptoms', 'FeverOnly', 'OtherSymptoms', 'Mild', 'Moderate', 'Severe']
        self.label_encoder.fit(severity_order)
        y = self.label_encoder.transform(df['true_severity'])
        
        return X, y
    
    def train_model(self, dataset_path='dengue_research_dataset_v1.csv', cv_folds=5):
        """Train Random Forest model with optional cross-validation"""
        print("🔄 Training ML model...")
        
        X, y = self.prepare_training_data(dataset_path)
        
        # Optional: Cross-validation
        if cv_folds > 0:
            print(f"📊 Performing {cv_folds}-fold cross-validation...")
            cv_scores = cross_val_score(
                RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced'),
                X, y, cv=cv_folds, scoring='accuracy'
            )
            print(f"  CV Accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std()*2:.3f})")
        
        # Train final model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X, y)
        
        # Save model and encoder
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.label_encoder, self.encoder_path)
        
        # Calculate accuracy
        train_accuracy = self.model.score(X, y)
        print(f"✅ Model trained with {train_accuracy*100:.1f}% training accuracy")
        print(f"💾 Model saved to: {self.model_path}")
        
        # Print feature importance
        self.print_feature_importance()
        
        return train_accuracy
    
    def load_model(self):
        """Load trained model"""
        try:
            self.model = joblib.load(self.model_path)
            self.label_encoder = joblib.load(self.encoder_path)
            print(f"✅ ML model loaded from {self.model_path}")
            print(f"📊 Model info: {self.get_model_info()}")
            return True
        except Exception as e:
            print(f"❌ No trained model found: {e}")
            print("⚠️ Using rule-based system only")
            return False
    
    def predict(self, symptoms_dict):
        """Predict severity from symptoms dictionary"""
        if not self.model or not self.label_encoder:
            return None, 0.0, {}
        
        try:
            # Convert chatbot symptoms to ML features
            features = self._convert_symptoms_to_features(symptoms_dict)
            
            # Make prediction
            prediction_encoded = self.model.predict([features])[0]
            prediction_prob = self.model.predict_proba([features]).max()
            
            # Get all probabilities
            all_probs = self.model.predict_proba([features])[0]
            prob_dict = {
                self.label_encoder.inverse_transform([i])[0]: float(prob) 
                for i, prob in enumerate(all_probs)
            }
            
            # Decode prediction
            prediction = self.label_encoder.inverse_transform([prediction_encoded])[0]
            
            return prediction, prediction_prob, prob_dict
            
        except Exception as e:
            print(f"ML prediction error: {e}")
            return None, 0.0, {}
    
    def _convert_symptoms_to_features(self, symptoms_dict):
        """Convert chatbot symptoms to ML features"""
        features = np.zeros(len(self.feature_names))
        
        for i, feature in enumerate(self.feature_names):
            for chatbot_key, ml_key in self.symptom_map.items():
                if ml_key == feature:
                    if chatbot_key in symptoms_dict:
                        value = symptoms_dict[chatbot_key]
                        
                        # Handle special encoding for persistent vomiting
                        if feature == 'persistent_vomiting_encoded':
                            vomiting_map = {'none': 0, 'once': 1, 'frequent': 2, 'continuous': 3}
                            features[i] = vomiting_map.get(value, 0)
                        else:
                            features[i] = 1 if value == 1 else 0
                    break
        
        return features
    
    def print_feature_importance(self):
        """Print feature importance scores"""
        if not self.model:
            return
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔝 Feature Importance:")
        for _, row in importance_df.iterrows():
            feature_name = row['feature'].replace('_', ' ').title()
            print(f"  {feature_name:30s}: {row['importance']:.3f}")
    
    def get_model_info(self):
        """Get information about the trained model"""
        if not self.model:
            return "No model loaded"
        
        info = {
            'model_type': type(self.model).__name__,
            'n_features': len(self.feature_names),
            'n_classes': len(self.label_encoder.classes_) if self.label_encoder else 0,
            'classes': list(self.label_encoder.classes_) if self.label_encoder else [],
            'version': self.model_version
        }
        
        if hasattr(self.model, 'n_estimators'):
            info['n_estimators'] = self.model.n_estimators
        
        return info
    
    def retrain_with_new_data(self, new_data_path='research_summary.csv'):
        """Retrain model with new user data"""
        print("🔄 Retraining model with new user data...")
        
        try:
            # Load existing synthetic data
            synthetic = pd.read_csv('dengue_research_dataset_v1.csv')
            
            # Load new user data
            user_data = pd.read_csv(new_data_path)
            
            # Prepare user data (rename columns to match)
            column_mapping = {
                'fever': 'fever',
                'headache': 'headache',
                'eye_pain': 'eye_pain',
                'vomiting': 'vomiting',
                'persistent_vomiting': 'persistent_vomiting',
                'abdominal_pain': 'abdominal_pain',
                'bleeding': 'bleeding',
                'fatigue': 'fatigue',
                'fluid_accumulation': 'fluid_accumulation',
                'predicted_severity': 'true_severity'
            }
            
            user_data_clean = user_data.rename(columns=column_mapping)
            
            # Combine datasets
            combined = pd.concat([synthetic, user_data_clean], ignore_index=True)
            
            # Retrain
            self.train_model_from_dataframe(combined)
            
            print(f"✅ Model retrained with {len(combined)} total cases")
            
        except Exception as e:
            print(f"Retraining error: {e}")
    
    def train_model_from_dataframe(self, df):
        """Train model from DataFrame"""
        # Encode persistent vomiting
        vomiting_map = {'none': 0, 'once': 1, 'frequent': 2, 'continuous': 3}
        df['persistent_vomiting_encoded'] = df['persistent_vomiting'].map(vomiting_map)
        
        # Prepare features and target
        X = df[self.feature_names].fillna(0)
        
        self.label_encoder = LabelEncoder()
        severity_order = ['NoSymptoms', 'FeverOnly', 'OtherSymptoms', 'Mild', 'Moderate', 'Severe']
        self.label_encoder.fit(severity_order)
        y = self.label_encoder.transform(df['true_severity'])
        
        # Train
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        self.model.fit(X, y)
        
        # Save
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.label_encoder, self.encoder_path)

# Train model if run directly
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 DENGUE ML MODEL TRAINING")
    print("=" * 60)
    
    predictor = DengueMLPredictor()
    
    # Train with 5-fold cross-validation
    accuracy = predictor.train_model(cv_folds=5)
    
    print("\n" + "=" * 60)
    print(f"🎯 Model training complete!")
    print(f"📊 Training Accuracy: {accuracy*100:.1f}%")
    print(f"💾 Model saved: dengue_model.pkl")
    print("=" * 60)