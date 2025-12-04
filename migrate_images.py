import os
import shutil
from path import Path

def migrate_images():
    """Migre les images de uploads/ vers data/uploads/"""
    
    # Ancien chemin
    old_uploads = Path('uploads')
    
    # Nouveau chemin
    new_uploads = Path('data/uploads')
    
    if not old_uploads.exists():
        print("❌ Ancien dossier uploads/ non trouvé")
        return
    
    # Créer la nouvelle structure
    new_uploads.makedirs_p()
    (new_uploads / 'troncons').makedirs_p()
    (new_uploads / 'taudis').makedirs_p()
    
    # Migrer les images
    migrated = 0
    
    # Migrer troncons
    old_troncons = old_uploads / 'troncons'
    if old_troncons.exists():
        for img in old_troncons.files('*.jpg') + old_troncons.files('*.png'):
            shutil.copy2(img, new_uploads / 'troncons' / img.name)
            migrated += 1
            print(f"✅ Migré: {img.name}")
    
    # Migrer taudis
    old_taudis = old_uploads / 'taudis'
    if old_taudis.exists():
        for img in old_taudis.files('*.jpg') + old_taudis.files('*.png'):
            shutil.copy2(img, new_uploads / 'taudis' / img.name)
            migrated += 1
            print(f"✅ Migré: {img.name}")
    
    print(f"\n🎉 Migration terminée: {migrated} images migrées")
    print(f"📁 Ancien: {old_uploads}")
    print(f"📁 Nouveau: {new_uploads}")

if __name__ == '__main__':
    migrate_images()