import os
import shutil
from pathlib import Path

def clean_logs():
    # Caminho para a pasta de logs
    logs_dir = Path("logs")
    
    # Se a pasta existe, remove todos os arquivos
    if logs_dir.exists():
        for file in logs_dir.glob("*.log"):
            try:
                file.unlink()
                print(f"Deleted: {file}")
            except Exception as e:
                print(f"Error deleting {file}: {e}")
                
    print("Logs cleaned successfully!")

if __name__ == "__main__":
    clean_logs()
