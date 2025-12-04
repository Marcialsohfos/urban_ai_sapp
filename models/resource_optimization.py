# resource_optimization.py
import numpy as np
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

class UrbanResourceOptimizer:
    def __init__(self):
        self.scaler = StandardScaler()
    
    def optimize_lighting(self, data):
        """Optimise l'éclairage public"""
        # Regroupement des tronçons par similarité
        features = data[['linéaire_ml', 'points_lumineux', 'traffic_estimate']].values
        features_scaled = self.scaler.fit_transform(features)
        
        # Clustering pour regrouper les tronçons similaires
        kmeans = KMeans(n_clusters=3, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)
        
        # Recommandations par cluster
        recommendations = []
        for i in range(3):
            cluster_data = data[clusters == i]
            avg_lights = cluster_data['points_lumineux'].mean()
            avg_length = cluster_data['linéaire_ml'].mean()
            
            # Calcul de l'éclairage optimal
            optimal_lights = max(10, int(avg_length / 30))  # 1 point tous les 30m
            
            recommendations.append({
                'cluster': i,
                'troncons': len(cluster_data),
                'eclairage_actuel_moyen': avg_lights,
                'eclairage_recommande': optimal_lights,
                'economie_potentielle': avg_lights - optimal_lights,
                'troncons_cibles': cluster_data['tronçon de voirie'].tolist()
            })
        
        return recommendations
    
    def predict_infrastructure_degradation(self, data):
        """Prédit la dégradation future des infrastructures"""
        # Simple modèle linéaire pour l'exemple
        degradation_rate = 0.05  # 5% de dégradation par an
        
        predictions = []
        for _, row in data.iterrows():
            current_state = row.get('etat_actuel', 0.8)  # 0-1, 1 = parfait
            age = row.get('age_infrastructure', 10)
            
            future_state = current_state * (1 - degradation_rate) ** 3  # 3 ans
            
            priority = 'Haute' if future_state < 0.5 else 'Moyenne' if future_state < 0.7 else 'Basse'
            
            predictions.append({
                'troncon': row['tronçon de voirie'],
                'etat_actuel': current_state,
                'etat_pred_3_ans': future_state,
                'priorite_intervention': priority,
                'annee_recommandee': 2024 + (3 if priority == 'Haute' else 5)
            })
        
        return predictions