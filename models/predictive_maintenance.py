# predictive_maintenance.py
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib

class MaintenancePredictor:
    def __init__(self):
        self.model = None
        self.features = [
            'linéaire_ml', 'classe_voirie_encoded', 
            'points_lumineux', 'age_infrastructure',
            'traffic_estimate', 'precipitation'
        ]
    
    def prepare_features(self, df):
        """Prépare les données pour la prédiction"""
        # Encodage des classes de voirie
        class_mapping = {'Primaire': 2, 'Secondaire': 1, 'Tertiaire': 0}
        df['classe_voirie_encoded'] = df['classe de voirie'].map(class_mapping)
        
        # Calcul de l'âge estimé
        df['age_infrastructure'] = 2024 - df.get('annee_construction', 2010)
        
        # Estimation du trafic
        df['traffic_estimate'] = df['points_lumineux'] * 100  # Estimation
        
        return df
    
    def train(self, X, y):
        """Entraîne le modèle"""
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
        
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)
        
        # Sauvegarde du modèle
        joblib.dump(self.model, 'models/maintenance_model.pkl')
        
        return self.model.score(X_test, y_test)
    
    def predict_priority(self, troncon_data):
        """Prédit la priorité de maintenance"""
        priority_labels = {
            0: 'Basse priorité',
            1: 'Priorité moyenne', 
            2: 'Haute priorité',
            3: 'Urgence'
        }
        
        prediction = self.model.predict_proba([troncon_data])
        priority_level = np.argmax(prediction)
        
        return {
            'niveau': priority_level,
            'label': priority_labels.get(priority_level, 'Inconnu'),
            'probabilite': float(prediction[0][priority_level]),
            'details': prediction[0].tolist()
        }