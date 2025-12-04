from setuptools import setup, find_packages

setup(
    name="urban-ai_sapp",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        'Flask==2.3.3',
        'gunicorn==21.2.0',
        'Werkzeug==2.3.7',
        'numpy==1.24.3',
        'pandas==1.5.3',
        'openpyxl==3.1.2',
        'scikit-learn==1.3.0',
        'joblib==1.3.1',
        'Pillow==10.0.0',
        'python-dotenv==1.0.0',
        'pyyaml==6.0'
    ]
)