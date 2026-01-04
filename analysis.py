import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import warnings
warnings.filterwarnings('ignore')

class DengueDataAnalyzer:
    def __init__(self, dataset_path='dengue_research_dataset_v1.csv'):
        self.df = pd.read_csv(dataset_path)
        self.setup_visualization()
        
    def setup_visualization(self):
        """Setup visualization style"""
        plt.style.use('seaborn-v0_8-darkgrid')
        sns.set_palette("husl")
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 12
        
    def basic_statistics(self):
        """Generate basic statistics"""
        print("=" * 60)
        print("DATASET BASIC STATISTICS")
        print("=" * 60)
        
        print(f"\n📊 Dataset Shape: {self.df.shape}")
        print(f"📅 Time Range: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}")
        
        print("\n🧪 SEVERITY DISTRIBUTION:")
        severity_dist = self.df['true_severity'].value_counts()
        print(severity_dist)
        
        print("\n👥 DEMOGRAPHICS:")
        print(f"Average Age: {self.df['age'].mean():.1f} ± {self.df['age'].std():.1f}")
        print(f"Gender Distribution (0=Female, 1=Male):")
        print(self.df['gender'].value_counts())
        
        print("\n🌡️ TEMPERATURE STATISTICS:")
        print(f"Average: {self.df['temperature'].mean():.1f}°C")
        print(f"Range: {self.df['temperature'].min():.1f}°C - {self.df['temperature'].max():.1f}°C")
        
        print("\n🩸 PLATELET COUNT:")
        print(f"Average: {self.df['platelet_count'].mean():,.0f}")
        print(f"< 50,000: {(self.df['platelet_count'] < 50000).sum()} patients")
        print(f"< 100,000: {(self.df['platelet_count'] < 100000).sum()} patients")
        
        return {
            'total_patients': len(self.df),
            'severity_distribution': severity_dist.to_dict(),
            'avg_age': self.df['age'].mean(),
            'gender_dist': self.df['gender'].value_counts().to_dict()
        }
    
    def symptom_analysis(self):
        """Analyze symptom patterns"""
        print("\n" + "=" * 60)
        print("SYMPTOM ANALYSIS")
        print("=" * 60)
        
        symptoms = ['fever', 'headache', 'eye_pain', 'vomiting', 'abdominal_pain',
                   'bleeding', 'fatigue', 'fluid_accumulation', 'rash', 'joint_pain']
        
        symptom_stats = {}
        for symptom in symptoms:
            prevalence = self.df[symptom].mean() * 100
            symptom_stats[symptom] = prevalence
            print(f"{symptom.replace('_', ' ').title():20s}: {prevalence:.1f}%")
        
        # Symptom co-occurrence
        print("\n📈 TOP SYMPTOM COMBINATIONS:")
        
        # Most common combination
        symptom_cols = symptoms[:9]  # Core symptoms
        self.df['symptom_count'] = self.df[symptom_cols].sum(axis=1)
        
        print(f"Average symptoms per patient: {self.df['symptom_count'].mean():.1f}")
        print(f"Patients with 0 symptoms: {(self.df['symptom_count'] == 0).sum()}")
        print(f"Patients with 5+ symptoms: {(self.df['symptom_count'] >= 5).sum()}")
        
        return symptom_stats
    
    def chatbot_performance(self):
        """Evaluate chatbot performance against ground truth"""
        print("\n" + "=" * 60)
        print("CHATBOT (RULE-BASED) PERFORMANCE EVALUATION")
        print("=" * 60)
        
        # Encode severity labels
        severity_order = ['NoSymptoms', 'FeverOnly', 'OtherSymptoms', 'Mild', 'Moderate', 'Severe']
        le = LabelEncoder()
        le.fit(severity_order)
        
        # Only include cases where chatbot made a prediction
        eval_df = self.df.dropna(subset=['chatbot_severity', 'true_severity'])
        
        y_true = le.transform(eval_df['true_severity'])
        y_pred = le.transform(eval_df['chatbot_severity'])
        
        # Accuracy
        accuracy = accuracy_score(y_true, y_pred)
        print(f"\n📊 Chatbot Accuracy: {accuracy:.3f} ({accuracy*100:.1f}%)")
        
        # Confusion matrix
        cm = confusion_matrix(y_true, y_pred, labels=le.transform(severity_order))
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                   xticklabels=le.classes_, yticklabels=le.classes_)
        plt.title('Confusion Matrix: Chatbot vs Ground Truth')
        plt.ylabel('True Severity')
        plt.xlabel('Predicted Severity')
        plt.tight_layout()
        plt.savefig('confusion_matrix_chatbot.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Classification report
        print("\n📋 Classification Report:")
        report = classification_report(y_true, y_pred, target_names=le.classes_, output_dict=True)
        
        for severity in severity_order:
            if severity in report:
                prec = report[severity]['precision']
                rec = report[severity]['recall']
                f1 = report[severity]['f1-score']
                print(f"{severity:15s}: Precision={prec:.3f}, Recall={rec:.3f}, F1={f1:.3f}")
        
        # Error analysis
        errors = eval_df[eval_df['chatbot_severity'] != eval_df['true_severity']]
        print(f"\n❌ Misclassified Cases: {len(errors)}/{len(eval_df)} ({len(errors)/len(eval_df)*100:.1f}%)")
        
        if not errors.empty:
            print("\nMost common error patterns:")
            error_patterns = errors.groupby(['true_severity', 'chatbot_severity']).size().nlargest(5)
            print(error_patterns)
        
        return {
            'accuracy': accuracy,
            'confusion_matrix': cm.tolist(),
            'misclassification_rate': len(errors)/len(eval_df)
        }
    
    def train_and_evaluate_ml_model(self):
        """Train and evaluate ML model"""
        print("\n" + "=" * 60)
        print("MACHINE LEARNING MODEL TRAINING & EVALUATION")
        print("=" * 60)
        
        # Prepare data
        features = ['fever', 'headache', 'eye_pain', 'vomiting', 'abdominal_pain',
                   'bleeding', 'fatigue', 'fluid_accumulation']
        
        # Encode persistent vomiting
        df_encoded = self.df.copy()
        vomiting_map = {'none': 0, 'once': 1, 'frequent': 2, 'continuous': 3}
        df_encoded['persistent_vomiting_encoded'] = df_encoded['persistent_vomiting'].map(vomiting_map)
        features.append('persistent_vomiting_encoded')
        
        # Prepare X and y
        X = df_encoded[features].fillna(0)
        
        # Encode severity for ML
        severity_order = ['NoSymptoms', 'FeverOnly', 'OtherSymptoms', 'Mild', 'Moderate', 'Severe']
        le = LabelEncoder()
        le.fit(severity_order)
        y = le.transform(df_encoded['true_severity'])
        
        # Split data
        try:
           X_train, X_test, y_train, y_test = train_test_split(
               X, y, test_size=0.3, random_state=42, stratify=y
           )
        except ValueError:
        # If stratification fails due to imbalanced classes, use random split
            print("⚠️ Warning: Some classes have too few samples. Using random split instead.")
            X_train, X_test, y_train, y_test = train_test_split(
                 X, y, test_size=0.3, random_state=42
            )
        
        # Train Random Forest
        rf = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
        rf.fit(X_train, y_train)
        
        # Predictions
        y_pred_rf = rf.predict(X_test)
        
        # Calculate accuracy
        rf_accuracy = accuracy_score(y_test, y_pred_rf)
        print(f"\n🌲 Random Forest Accuracy: {rf_accuracy:.3f} ({rf_accuracy*100:.1f}%)")
        
        # Confusion matrix for ML
        cm_ml = confusion_matrix(y_test, y_pred_rf, labels=le.transform(severity_order))
        
        plt.figure(figsize=(10, 8))
        sns.heatmap(cm_ml, annot=True, fmt='d', cmap='Greens',
                   xticklabels=le.classes_, yticklabels=le.classes_)
        plt.title('Confusion Matrix: Random Forest Model')
        plt.ylabel('True Severity')
        plt.xlabel('Predicted Severity')
        plt.tight_layout()
        plt.savefig('confusion_matrix_ml.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'feature': features,
            'importance': rf.feature_importances_
        }).sort_values('importance', ascending=False)
        
        print("\n🔝 Top 5 Most Important Features for ML Model:")
        print(feature_importance.head(5).to_string(index=False))
        
        # Visualize feature importance
        plt.figure(figsize=(10, 6))
        top_features = feature_importance.head(10)
        plt.barh(top_features['feature'], top_features['importance'])
        plt.xlabel('Feature Importance')
        plt.title('Top 10 Features for Dengue Severity Prediction (ML)')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('feature_importance_ml.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return {
            'ml_accuracy': rf_accuracy,
            'top_features': feature_importance.head(10).to_dict('records')
        }
    
    def compare_chatbot_vs_ml(self, chatbot_perf, ml_perf):
        """Compare chatbot vs ML performance"""
        print("\n" + "=" * 60)
        print("CHATBOT vs MACHINE LEARNING COMPARISON")
        print("=" * 60)
        
        chatbot_acc = chatbot_perf['accuracy']
        ml_acc = ml_perf['ml_accuracy']
        improvement = ml_acc - chatbot_acc
        
        print(f"\n🤖 Chatbot (Rule-Based) Accuracy: {chatbot_acc:.3f} ({chatbot_acc*100:.1f}%)")
        print(f"🌲 ML (Random Forest) Accuracy: {ml_acc:.3f} ({ml_acc*100:.1f}%)")
        print(f"📈 Improvement with ML: {improvement:.3f} ({improvement*100:.1f}%)")
        
        # Visual comparison
        methods = ['Rule-Based Chatbot', 'ML Model']
        accuracies = [chatbot_acc, ml_acc]
        
        plt.figure(figsize=(8, 6))
        bars = plt.bar(methods, accuracies, color=['#FF6B6B', '#4ECDC4'])
        plt.ylabel('Accuracy')
        plt.title('Performance Comparison: Chatbot vs ML Model')
        plt.ylim(0, 1.0)
        
        # Add value labels on bars
        for bar, acc in zip(bars, accuracies):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01,
                    f'{acc:.3f}', ha='center', va='bottom')
        
        plt.tight_layout()
        plt.savefig('performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.show()
        
        return {
            'chatbot_accuracy': chatbot_acc,
            'ml_accuracy': ml_acc,
            'improvement': improvement
        }
    
    def generate_research_report(self):
        """Generate comprehensive research report"""
        print("\n" + "=" * 60)
        print("GENERATING COMPREHENSIVE RESEARCH REPORT")
        print("=" * 60)
        
        # Run all analyses
        stats = self.basic_statistics()
        symptom_stats = self.symptom_analysis()
        chatbot_perf = self.chatbot_performance()
        ml_perf = self.train_and_evaluate_ml_model()
        comparison = self.compare_chatbot_vs_ml(chatbot_perf, ml_perf)
        
        # Generate detailed report
        report = f"""
        {'='*60}
        DENGUE TRIAGE SYSTEM: RULE-BASED vs MACHINE LEARNING
        {'='*60}
        
        1. DATASET OVERVIEW
        {'-'*40}
        Total Patients: {stats['total_patients']}
        Time Period: {self.df['timestamp'].min()} to {self.df['timestamp'].max()}
        
        Severity Distribution:
        {pd.Series(stats['severity_distribution']).to_string()}
        
        Demographics:
        Average Age: {stats['avg_age']:.1f} years
        Gender: {stats['gender_dist']}
        
        2. SYMPTOM PREVALENCE
        {'-'*40}
        Most Common Symptoms:
        {pd.Series(symptom_stats).nlargest(5).to_string()}
        
        Average symptoms per patient: {self.df['symptom_count'].mean():.1f}
        
        3. RULE-BASED CHATBOT PERFORMANCE
        {'-'*40}
        Overall Accuracy: {chatbot_perf['accuracy']:.3f} ({chatbot_perf['accuracy']*100:.1f}%)
        Misclassification Rate: {chatbot_perf['misclassification_rate']:.3f}
        
        4. MACHINE LEARNING MODEL
        {'-'*40}
        Model Type: Random Forest Classifier
        Training Accuracy: {ml_perf['ml_accuracy']:.3f} ({ml_perf['ml_accuracy']*100:.1f}%)
        
        Top Predictive Features:
        {pd.DataFrame(ml_perf['top_features']).to_string(index=False)}
        
        5. PERFORMANCE COMPARISON
        {'-'*40}
        Rule-Based Chatbot: {comparison['chatbot_accuracy']:.3f}
        ML Model: {comparison['ml_accuracy']:.3f}
        Improvement: {comparison['improvement']:.3f} ({comparison['improvement']*100:.1f}%)
        
        6. KEY FINDINGS
        {'-'*40}
        • The rule-based chatbot achieves {chatbot_perf['accuracy']*100:.1f}% accuracy
        • Machine learning shows potential improvement of {comparison['improvement']*100:.1f}%
        • Most common symptom: Fever ({symptom_stats.get('fever', 0):.1f}%)
        • Critical indicators for severe dengue: Fluid accumulation and bleeding
        • ML models can learn complex patterns beyond rule-based logic
        
        7. RECOMMENDATIONS
        {'-'*40}
        • Implement hybrid approach: ML predictions with rule-based fallback
        • Use ML confidence thresholds for decision making
        • Regularly retrain models with new user data
        • Consider ensemble methods for improved accuracy
        • Clinical validation with real patient outcomes
        
        8. VISUALIZATIONS GENERATED
        {'-'*40}
        • confusion_matrix_chatbot.png - Chatbot performance
        • confusion_matrix_ml.png - ML model performance
        • feature_importance_ml.png - ML feature importance
        • performance_comparison.png - Chatbot vs ML comparison
        {'='*60}
        """
        
        # Save report
        with open('comprehensive_research_report.txt', 'w') as f:
            f.write(report)
        
        print("\n✅ Comprehensive report saved as 'comprehensive_research_report.txt'")
        print("✅ All visualizations saved as PNG files")
        
        return report

# Run complete analysis
if __name__ == "__main__":
    print("Starting comprehensive analysis of Dengue Triage System...")
    analyzer = DengueDataAnalyzer('dengue_research_dataset_v1.csv')
    report = analyzer.generate_research_report()
    print(report)