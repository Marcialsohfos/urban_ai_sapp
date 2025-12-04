# backup.py
import os
import shutil
from datetime import datetime

def backup_data():
    """Sauvegarde des données vers Google Drive/Dropbox"""
    
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"{backup_dir}/urban_ai_backup_{timestamp}.zip"
    
    # Fichiers à sauvegarder
    files_to_backup = [
        "data/indicateurs_urbains.xlsx",
        "uploads/",
        "models/"
    ]
    
    # Créer l'archive
    shutil.make_archive(
        backup_file.replace('.zip', ''),
        'zip',
        root_dir='.',
        base_dir=files_to_backup
    )
    
    print(f"✅ Backup créé: {backup_file}")
    
    # Upload vers Google Drive (optionnel)
    # upload_to_drive(backup_file)