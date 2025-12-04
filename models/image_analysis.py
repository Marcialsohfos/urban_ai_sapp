# image_analysis.py
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

class RoadDefectDetector:
    def __init__(self, model_path='models/defect_detector.h5'):
        self.model = load_model(model_path)
        self.classes = ['bon_etat', 'nids_poule', 'fissures', 'deformation']
    
    def preprocess_image(self, img_path):
        """Prépare l'image pour l'analyse"""
        img = image.load_img(img_path, target_size=(224, 224))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0)
        img_array /= 255.0
        
        return img_array
    
    def analyze_road_image(self, img_path):
        """Analyse une image de route"""
        processed_img = self.preprocess_image(img_path)
        predictions = self.model.predict(processed_img)
        class_idx = np.argmax(predictions[0])
        
        return {
            'etat': self.classes[class_idx],
            'confiance': float(predictions[0][class_idx]),
            'details': dict(zip(self.classes, predictions[0].tolist()))
        }
    
    def detect_potholes(self, img_path):
        """Détection spécifique des nids-de-poule"""
        img = cv2.imread(img_path)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Détection des contours
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)
        
        # Trouver les contours
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filtrer les contours (nids-de-poule)
        potholes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if 100 < area < 10000:  # Taille raisonnable pour un nid-de-poule
                x, y, w, h = cv2.boundingRect(contour)
                potholes.append({
                    'position': {'x': x, 'y': y},
                    'dimensions': {'largeur': w, 'hauteur': h},
                    'superficie': area
                })
        
        return {
            'nombre_nids_poule': len(potholes),
            'superficie_totale': sum(p['superficie'] for p in potholes),
            'details': potholes
        }