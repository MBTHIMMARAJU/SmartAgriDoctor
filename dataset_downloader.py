import os
import kaggle
from kaggle.api.kaggle_api_extended import KaggleApi
import zipfile

def download_dataset():
    """Download the plant disease dataset from Kaggle"""
    try:
        # Configure Kaggle API
        api = KaggleApi()
        api.authenticate()
        
        # Download dataset
        dataset = 'vipoooool/new-plant-diseases-dataset'
        download_path = 'dataset/'
        
        print("Downloading dataset...")
        api.dataset_download_files(dataset, path=download_path, unzip=True)
        print("Dataset downloaded successfully!")
        
        return True
    except Exception as e:
        print(f"Error downloading dataset: {e}")
        return False

def setup_dataset_structure():
    """Create necessary directory structure"""
    os.makedirs('dataset', exist_ok=True)
    os.makedirs('static/uploads', exist_ok=True)
    os.makedirs('models', exist_ok=True)

if __name__ == "__main__":
    setup_dataset_structure()
    download_dataset()