#!/usr/bin/env python3
"""
Script de configuration pour Urban AI avec structure data/uploads/
"""

import os
import sys
import shutil

def setup_project():
    print("="*60)
    print("🔧 CONFIGURATION URBAN AI - STRUCTURE OPTIMISÉE")
    print("="*60)
    
    # 1. Créer la structure data/uploads/
    folders = [
        'models',
        'data',                    # Dossier data principal
        'data/uploads',           # Uploads DANS data/
        'data/uploads/troncons',  # Images tronçons
        'data/uploads/taudis',    # Images taudis
        'static/css',
        'static/js',
        'static/images',
        'templates',
        'temp'
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"✅ Dossier créé: {folder}")
    