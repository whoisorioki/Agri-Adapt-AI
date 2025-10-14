"""
Multi-Crop Model Training Pipeline
Unified framework for training Random Forest models across multiple crops
"""

import pandas as pd
import polars as pl
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
import joblib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiCropTrainer:
    """
    Unified training pipeline for multiple crop resilience models
    Supports: Sorghum, Millet, Wheat, Beans, Potato
    """
    
    def __init__(self, data_dir: str = "data", models_dir: str = "models"):
        self.data_dir = Path(data_dir)
        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(exist_ok=True, parents=True)
        
        # Crop-specific configurations
        self.crop_configs = {
            'sorghum': {
                'target_r2': 0.82,
                'priority': 1,
                'features': 'drought_optimized',
                'special_handling': 'asal_calibration'
            },
            'millet': {
                'target_r2': 0.80,
                'priority': 1, 
                'features': 'heat_stress_optimized',
                'special_handling': 'smallholder_focus'
            },
            'wheat': {
                'target_r2': 0.85,
                'priority': 1,
                'features': 'commercial_optimized', 
                'special_handling': 'highland_calibration'
            },
            'beans': {
                'target_r2': 0.75,
                'priority': 2,
                'features': 'intercropping_optimized',
                'special_handling': 'nutrition_focus'
            },
            'potato': {
                'target_r2': 0.75,
                'priority': 2,
                'features': 'highland_optimized',
                'special_handling': 'cash_crop_focus'
            }
        }
        
        # Base feature set (consistent with MVP)
        self.base_features = [
            'Monthly_Rainfall_mm',
            'Monthly_Temperature_C', 
            'Monthly_Humidity_Percent',
            'Monthly_Evapotranspiration_mm',
            'Monthly_Water_Stress_Index',
            'Soil_pH_H2O',
            'Soil_Organic_Carbon'
        ]
        
        # Trained models storage
        self.trained_models = {}
        self.model_performance = {}
    
    def load_master_dataset(self) -> pl.DataFrame:
        """
        Load the master environmental dataset
        """
        master_path = self.data_dir / "master_water_scarcity_dataset.csv"
        
        if not master_path.exists():
            raise FileNotFoundError(f"Master dataset not found: {master_path}")
        
        logger.info(f"Loading master dataset from {master_path}")
        
        # Load with Polars for efficiency
        df = pl.read_csv(master_path)
        logger.info(f"Loaded {len(df)} environmental records")
        
        return df
    
    def load_crop_yield_data(self, crop_name: str) -> pl.DataFrame:
        """
        Load crop-specific yield data from KALRO collection
        """
        crop_files = list(self.data_dir.glob(f"external/{crop_name}_*.csv"))
        
        if not crop_files:
            logger.warning(f"No yield data files found for {crop_name}")
            return None
        
        # Combine all crop data files
        crop_dfs = []
        for file_path in crop_files:
            df = pl.read_csv(file_path)
            crop_dfs.append(df)
        
        # Concatenate all crop data
        combined_df = pl.concat(crop_dfs)
        
        logger.info(f"Loaded {len(combined_df)} yield records for {crop_name}")
        return combined_df
    
    def prepare_training_data(self, crop_name: str) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare feature matrix and target vector for model training
        """
        logger.info(f"Preparing training data for {crop_name}")
        
        # Load environmental data
        env_data = self.load_master_dataset()
        
        # Load crop yield data
        crop_data = self.load_crop_yield_data(crop_name)
        
        if crop_data is None:
            raise ValueError(f"No yield data available for {crop_name}")
        
        # Join environmental and crop data
        # Match on County and Year
        joined_data = env_data.join(
            crop_data.select(['County', 'Year', 'Yield_tonnes_ha']),
            on=['County', 'Year'],
            how='inner'
        )
        
        logger.info(f"Joined dataset: {len(joined_data)} records")
        
        if len(joined_data) == 0:
            raise ValueError(f"No matching records found for {crop_name}")
        
        # Prepare features
        feature_cols = self._get_crop_features(crop_name)
        
        # Convert to pandas for sklearn compatibility
        df_pandas = joined_data.to_pandas()
        
        # Feature matrix
        X = df_pandas[feature_cols].values
        
        # Target vector
        y = df_pandas['Yield_tonnes_ha'].values
        
        # Handle missing values
        mask = ~(pd.isnull(X).any(axis=1) | pd.isnull(y))
        X = X[mask]
        y = y[mask]
        
        logger.info(f"Final training set: {len(X)} samples, {X.shape[1]} features")
        
        return X, y, feature_cols
    
    def _get_crop_features(self, crop_name: str) -> List[str]:
        """
        Get crop-specific feature set based on crop characteristics
        """
        features = self.base_features.copy()
        
        # Add crop-specific features based on configuration
        config = self.crop_configs[crop_name]
        
        if config['features'] == 'drought_optimized':
            # Add features important for drought-tolerant crops
            features.extend([
                'Monthly_Irrigation_Volume_Liters_Ha',
                'Water_Scarcity_Score'
            ])
        
        elif config['features'] == 'heat_stress_optimized':
            # Add features for heat-sensitive crops
            features.extend([
                'Monthly_Heat_Stress_Days',
                'Monthly_Crop_Yield_Impact_Percent'
            ])
        
        elif config['features'] == 'commercial_optimized':
            # Add features for commercial crop management
            features.extend([
                'Agricultural_Risk_Index',
                'Irrigation_Priority_Score'
            ])
        
        elif config['features'] == 'highland_optimized':
            # Add features for highland crops
            features.extend([
                'Monthly_Temperature_C',  # Already included, emphasize
                'Monthly_Humidity_Percent'
            ])
        
        # Remove duplicates while preserving order
        features = list(dict.fromkeys(features))
        
        return features
    
    def train_crop_model(self, crop_name: str) -> Dict:
        """
        Train Random Forest model for specific crop
        """
        logger.info(f"🌾 Training {crop_name.title()} resilience model")
        
        # Prepare training data
        X, y, feature_names = self.prepare_training_data(crop_name)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Configure model based on crop characteristics
        model_params = self._get_crop_model_params(crop_name)
        
        # Train Random Forest model
        model = RandomForestRegressor(**model_params, random_state=42)
        model.fit(X_train_scaled, y_train)
        
        # Make predictions
        y_pred_train = model.predict(X_train_scaled)
        y_pred_test = model.predict(X_test_scaled)
        
        # Calculate metrics
        train_r2 = r2_score(y_train, y_pred_train)
        test_r2 = r2_score(y_test, y_pred_test)
        test_rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
        test_mae = mean_absolute_error(y_test, y_pred_test)
        
        # Cross-validation
        cv_scores = cross_val_score(model, X_train_scaled, y_train, cv=5, scoring='r2')
        
        # Performance metrics
        performance = {
            'crop_name': crop_name,
            'train_r2': train_r2,
            'test_r2': test_r2,
            'test_rmse': test_rmse,
            'test_mae': test_mae,
            'cv_r2_mean': cv_scores.mean(),
            'cv_r2_std': cv_scores.std(),
            'target_r2': self.crop_configs[crop_name]['target_r2'],
            'target_achieved': test_r2 >= self.crop_configs[crop_name]['target_r2'],
            'n_samples': len(X),
            'n_features': len(feature_names),
            'feature_names': feature_names,
            'trained_at': datetime.now().isoformat()
        }
        
        # Feature importance
        feature_importance = dict(zip(feature_names, model.feature_importances_))
        performance['feature_importance'] = sorted(
            feature_importance.items(), key=lambda x: x[1], reverse=True
        )
        
        # Store model and components
        model_data = {
            'model': model,
            'scaler': scaler,
            'feature_names': feature_names,
            'performance': performance,
            'crop_config': self.crop_configs[crop_name]
        }
        
        # Save model
        model_path = self.models_dir / f"{crop_name}_resilience_model.joblib"
        joblib.dump(model_data, model_path)
        
        # Store in memory
        self.trained_models[crop_name] = model_data
        self.model_performance[crop_name] = performance
        
        # Log results
        status = "✅" if performance['target_achieved'] else "⚠️"
        logger.info(f"{status} {crop_name.title()} Model - R²: {test_r2:.3f} (Target: {performance['target_r2']:.3f})")
        logger.info(f"   RMSE: {test_rmse:.3f}, MAE: {test_mae:.3f}")
        logger.info(f"   Model saved to: {model_path}")
        
        return performance
    
    def _get_crop_model_params(self, crop_name: str) -> Dict:
        """
        Get crop-specific Random Forest parameters
        """
        base_params = {
            'n_estimators': 100,
            'max_depth': None,
            'min_samples_split': 5,
            'min_samples_leaf': 2,
            'n_jobs': -1
        }
        
        # Crop-specific tuning
        config = self.crop_configs[crop_name]
        
        if config['special_handling'] == 'asal_calibration':
            # More trees for drought-prone areas
            base_params['n_estimators'] = 150
            
        elif config['special_handling'] == 'highland_calibration':
            # Deeper trees for highland complexity
            base_params['max_depth'] = 15
            
        return base_params
    
    def train_all_priority_crops(self) -> Dict[str, Dict]:
        """
        Train models for all priority crops in Phase I
        """
        logger.info("🚀 Starting multi-crop model training pipeline")
        
        all_results = {}
        
        # Sort crops by priority
        sorted_crops = sorted(
            self.crop_configs.items(),
            key=lambda x: x[1]['priority']
        )
        
        for crop_name, config in sorted_crops:
            try:
                logger.info(f"\n--- Training {crop_name.title()} (Priority {config['priority']}) ---")
                
                result = self.train_crop_model(crop_name)
                all_results[crop_name] = result
                
                if result['target_achieved']:
                    logger.info(f"✅ {crop_name.title()} model meets target accuracy")
                else:
                    logger.warning(f"⚠️ {crop_name.title()} model below target - needs optimization")
                
            except Exception as e:
                logger.error(f"❌ Failed to train {crop_name} model: {e}")
                all_results[crop_name] = {
                    'status': 'failed',
                    'error': str(e),
                    'target_achieved': False
                }
        
        # Save training summary
        summary_path = self.models_dir / 'training_summary.json'
        with open(summary_path, 'w') as f:
            json.dump(all_results, f, indent=2, default=str)
        
        logger.info(f"\n📊 Training summary saved to: {summary_path}")
        
        return all_results
    
    def generate_comparison_report(self) -> Dict:
        """
        Generate comprehensive model comparison report
        """
        if not self.model_performance:
            logger.warning("No trained models available for comparison")
            return {}
        
        logger.info("📊 Generating multi-crop model comparison report")
        
        comparison = {
            'summary': {
                'total_models': len(self.model_performance),
                'successful_models': sum(1 for p in self.model_performance.values() 
                                       if p.get('target_achieved', False)),
                'average_r2': np.mean([p['test_r2'] for p in self.model_performance.values()]),
                'report_generated': datetime.now().isoformat()
            },
            'crop_performance': {}
        }
        
        for crop_name, perf in self.model_performance.items():
            comparison['crop_performance'][crop_name] = {
                'test_r2': perf['test_r2'],
                'target_r2': perf['target_r2'],
                'target_achieved': perf['target_achieved'],
                'cv_r2_mean': perf['cv_r2_mean'],
                'n_samples': perf['n_samples'],
                'top_features': perf['feature_importance'][:3]  # Top 3 features
            }
        
        # Save comparison report
        report_path = self.models_dir / 'model_comparison_report.json'
        with open(report_path, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        logger.info(f"Comparison report saved to: {report_path}")
        
        return comparison


def main():
    """
    Main execution function for multi-crop model training
    """
    print("🌾 Multi-Crop Model Training Pipeline")
    print("=" * 50)
    
    trainer = MultiCropTrainer()
    
    # Train all priority crops
    results = trainer.train_all_priority_crops()
    
    # Generate comparison report
    comparison = trainer.generate_comparison_report()
    
    # Print summary
    print("\n📊 Training Results Summary:")
    print("-" * 50)
    
    for crop_name, result in results.items():
        if 'test_r2' in result:
            status = "✅" if result['target_achieved'] else "⚠️"
            r2_score = result['test_r2']
            target = result['target_r2']
            samples = result['n_samples']
            
            print(f"{status} {crop_name.title():<8} | R²: {r2_score:.3f}/{target:.3f} | Samples: {samples:>4}")
        else:
            print(f"❌ {crop_name.title():<8} | FAILED: {result.get('error', 'Unknown error')}")
    
    if comparison.get('summary'):
        summary = comparison['summary']
        print(f"\n🎯 Overall Performance:")
        print(f"   Models Trained: {summary['total_models']}")
        print(f"   Targets Met: {summary['successful_models']}/{summary['total_models']}")
        print(f"   Average R²: {summary['average_r2']:.3f}")
    
    print("\n🚀 Multi-crop models ready for Phase I demo!")


if __name__ == "__main__":
    main()