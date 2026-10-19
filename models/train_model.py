import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import json
from pathlib import Path
from typing import Dict, List, Tuple
import random

class HybridRecommenderTrainer:
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.provider_mapping = {'aws': 0, 'azure': 1, 'gcp': 2}
        self.reverse_mapping = {0: 'aws', 1: 'azure', 2: 'gcp'}
        
    def generate_synthetic_data(self, num_samples: int = 10000) -> pd.DataFrame:
        """Generate synthetic training data with enhanced variance and special cases"""
        print("🔄 Generating enhanced synthetic training data...")
        
        data = []
        
        # Base patterns for different scenarios
        scenarios = [
            # Cost-sensitive scenarios
            {'cost_sensitivity': 'high', 'region': 'us-east-1', 'service': 'compute', 'preferred': 'aws'},
            {'cost_sensitivity': 'high', 'region': 'ap-south-1', 'service': 'compute', 'preferred': 'gcp'},
            {'cost_sensitivity': 'high', 'region': 'eu-west-1', 'service': 'compute', 'preferred': 'azure'},
            
            # Performance-sensitive scenarios
            {'cost_sensitivity': 'low', 'region': 'us-east-1', 'service': 'ml-workload', 'preferred': 'aws'},
            {'cost_sensitivity': 'low', 'region': 'eu-west-1', 'service': 'database', 'preferred': 'azure'},
            {'cost_sensitivity': 'low', 'region': 'ap-south-1', 'service': 'hpc', 'preferred': 'gcp'},
            
            # Balanced scenarios
            {'cost_sensitivity': 'medium', 'region': 'us-west-2', 'service': 'storage', 'preferred': 'aws'},
            {'cost_sensitivity': 'medium', 'region': 'eu-west-1', 'service': 'api-service', 'preferred': 'azure'},
        ]
        
        # Special case scenarios (10% of data)
        special_cases = [
            {'compliance_required': True, 'region': 'eu-west-1', 'preferred': 'azure'},
            {'performance_priority': True, 'service': 'ml-workload', 'preferred': 'aws'},
            {'data_sovereignty': True, 'region': 'ap-south-1', 'preferred': 'gcp'},
        ]
        
        for i in range(num_samples):
            # 10% chance for special cases
            if random.random() < 0.1 and i < len(special_cases):
                scenario = random.choice(scenarios)
                special_case = special_cases[i % len(special_cases)]
                scenario.update(special_case)
            else:
                scenario = random.choice(scenarios)
            
            # Generate features
            region = scenario['region']
            service_type = scenario['service']
            cost_sensitivity = scenario['cost_sensitivity']
            preferred_provider = scenario['preferred']
            
            # Generate realistic cost data with enhanced variance
            base_costs = {
                'aws': random.uniform(50, 200),
                'azure': random.uniform(45, 220),
                'gcp': random.uniform(40, 190)
            }
            
            # Add ±15% variance to all costs
            for provider in base_costs:
                variance = random.uniform(-0.15, 0.15)
                base_costs[provider] *= (1 + variance)
            
            # Adjust costs based on region
            regional_multipliers = {
                'us-east-1': 1.0,
                'us-west-2': 1.1,
                'eu-west-1': 1.2,
                'ap-south-1': 0.9,
                'ap-southeast-1': 1.0
            }
            
            multiplier = regional_multipliers.get(region, 1.0)
            for provider in base_costs:
                base_costs[provider] *= multiplier
            
            # Adjust based on service type
            service_multipliers = {
                'compute': 1.0,
                'storage': 0.3,
                'database': 2.0,
                'ml-workload': 3.0,
                'hpc': 4.0,
                'api-service': 1.2
            }
            
            service_mult = service_multipliers.get(service_type, 1.0)
            for provider in base_costs:
                base_costs[provider] *= service_mult
            
            # Special case adjustments
            if scenario.get('compliance_required', False):
                # Compliance requirements may override cost optimization
                if region == 'eu-west-1':
                    base_costs['azure'] *= 0.8  # Azure preferred for EU compliance
                elif region == 'ap-south-1':
                    base_costs['gcp'] *= 0.8  # GCP preferred for data sovereignty
                    
            if scenario.get('performance_priority', False):
                # Performance over cost
                if service_type == 'ml-workload':
                    base_costs['aws'] *= 0.7  # AWS preferred for ML
                elif service_type == 'hpc':
                    base_costs['gcp'] *= 0.7  # GCP preferred for HPC
                    
            if scenario.get('data_sovereignty', False):
                # Data sovereignty requirements
                if region == 'ap-south-1':
                    base_costs['gcp'] *= 0.6  # Strong preference for local provider
                elif region == 'eu-west-1':
                    base_costs['azure'] *= 0.7
                    
            # Add noise and bias based on preferred provider
            for provider in base_costs:
                if provider == preferred_provider:
                    base_costs[provider] *= random.uniform(0.7, 1.0)  # Make preferred cheaper
                else:
                    base_costs[provider] *= random.uniform(1.0, 1.4)  # Make others more expensive
            
            # Find best provider (lowest cost)
            best_provider = min(base_costs.items(), key=lambda x: x[1])[0]
            
            # Generate additional features
            workload_size = random.choice(['small', 'medium', 'large'])
            current_provider = random.choice(['aws', 'azure', 'gcp'])
            
            # Calculate relative costs
            min_cost = min(base_costs.values())
            max_cost = max(base_costs.values())
            cost_range = max_cost - min_cost if max_cost > min_cost else 1
            
            # Feature engineering
            features = {
                'region_us_east': 1 if region == 'us-east-1' else 0,
                'region_us_west': 1 if region == 'us-west-2' else 0,
                'region_eu_west': 1 if region == 'eu-west-1' else 0,
                'region_ap_south': 1 if region == 'ap-south-1' else 0,
                'region_ap_southeast': 1 if region == 'ap-southeast-1' else 0,
                
                'service_compute': 1 if service_type == 'compute' else 0,
                'service_storage': 1 if service_type == 'storage' else 0,
                'service_database': 1 if service_type == 'database' else 0,
                'service_ml': 1 if service_type == 'ml-workload' else 0,
                'service_hpc': 1 if service_type == 'hpc' else 0,
                'service_api': 1 if service_type == 'api-service' else 0,
                
                'cost_sensitivity_high': 1 if cost_sensitivity == 'high' else 0,
                'cost_sensitivity_medium': 1 if cost_sensitivity == 'medium' else 0,
                'cost_sensitivity_low': 1 if cost_sensitivity == 'low' else 0,
                
                'workload_small': 1 if workload_size == 'small' else 0,
                'workload_medium': 1 if workload_size == 'medium' else 0,
                'workload_large': 1 if workload_size == 'large' else 0,
                
                'current_aws': 1 if current_provider == 'aws' else 0,
                'current_azure': 1 if current_provider == 'azure' else 0,
                'current_gcp': 1 if current_provider == 'gcp' else 0,
                
                # Special case features
                'compliance_required': 1 if scenario.get('compliance_required', False) else 0,
                'performance_priority': 1 if scenario.get('performance_priority', False) else 0,
                'data_sovereignty': 1 if scenario.get('data_sovereignty', False) else 0,
                
                'aws_cost': base_costs['aws'],
                'azure_cost': base_costs['azure'],
                'gcp_cost': base_costs['gcp'],
                'cost_range': cost_range,
                'min_cost': min_cost,
                'max_cost': max_cost,
                
                'aws_relative_cost': (base_costs['aws'] - min_cost) / cost_range,
                'azure_relative_cost': (base_costs['azure'] - min_cost) / cost_range,
                'gcp_relative_cost': (base_costs['gcp'] - min_cost) / cost_range,
            }
            
            features['best_provider'] = best_provider
            data.append(features)
        
        df = pd.DataFrame(data)
        print(f"✅ Generated {len(df)} synthetic samples")
        return df
    
    def prepare_features(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare features and labels for training"""
        # Separate features and labels
        feature_columns = [col for col in df.columns if col != 'best_provider']
        self.feature_columns = feature_columns
        
        X = df[feature_columns].values
        y = df['best_provider'].map(self.provider_mapping).values
        
        return X, y
    
    def train_model(self, X: np.ndarray, y: np.ndarray) -> Dict:
        """Train the Random Forest model"""
        print("🤖 Training Random Forest model...")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Train model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        y_pred = self.model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"✅ Model trained with {accuracy:.3f} accuracy")
        
        # Feature importance
        feature_importance = dict(zip(self.feature_columns, self.model.feature_importances_))
        
        return {
            'accuracy': accuracy,
            'feature_importance': feature_importance,
            'classification_report': classification_report(y_test, y_pred, target_names=['aws', 'azure', 'gcp'])
        }
    
    def save_model(self, model_path: str = "models/recommender.pkl"):
        """Save the trained model and metadata"""
        Path("models").mkdir(exist_ok=True)
        
        # Save model
        joblib.dump(self.model, model_path)
        
        # Save metadata
        metadata = {
            'feature_columns': self.feature_columns,
            'provider_mapping': self.provider_mapping,
            'reverse_mapping': self.reverse_mapping,
            'model_type': 'RandomForestClassifier',
            'n_estimators': 100,
            'max_depth': 10
        }
        
        with open("models/metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        print(f"✅ Model saved to {model_path}")
        print(f"✅ Metadata saved to models/metadata.json")
    
    def run_training_pipeline(self):
        """Complete training pipeline"""
        print("🚀 Starting Hybrid Recommender Training Pipeline")
        print("=" * 60)
        
        # Generate synthetic data
        df = self.generate_synthetic_data(num_samples=10000)
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        # Train model
        results = self.train_model(X, y)
        
        # Save model
        self.save_model()
        
        print("\n📊 Training Results:")
        print(f"Accuracy: {results['accuracy']:.3f}")
        print("\n🔝 Top 10 Most Important Features:")
        sorted_features = sorted(results['feature_importance'].items(), key=lambda x: x[1], reverse=True)
        for feature, importance in sorted_features[:10]:
            print(f"  {feature}: {importance:.3f}")
        
        return results

if __name__ == "__main__":
    trainer = HybridRecommenderTrainer()
    trainer.run_training_pipeline()
