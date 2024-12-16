"""
Autenticação com a API do YouTube.
"""

import os
from typing import Optional
from pathlib import Path
import pickle
import json

from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from ..core.logger import ComponentLogger
from ..core.config import config
from ..core.exceptions import DownloadError

logger = ComponentLogger(__name__)

class YouTubeAuth:
    """
    Gerencia autenticação com YouTube.
    """
    
    # Escopos necessários
    SCOPES = [
        "https://www.googleapis.com/auth/youtube.readonly",
        "https://www.googleapis.com/auth/youtube.force-ssl"
    ]
    
    def __init__(self):
        """Inicializa autenticação."""
        self.credentials_dir = config.paths.BASE_DIR / "credentials"
        self.credentials_dir.mkdir(parents=True, exist_ok=True)
        
        self.token_path = self.credentials_dir / "youtube_token.pickle"
        self.credentials_path = self.credentials_dir / "youtube_credentials.json"
        
        self._credentials = None
    
    def _load_credentials(self) -> Optional[Credentials]:
        """
        Carrega credenciais salvas.
        
        Returns:
            Credenciais ou None se não encontradas/expiradas
        """
        if not self.token_path.exists():
            return None
            
        try:
            with open(self.token_path, "rb") as token:
                creds = pickle.load(token)
                
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    return None
                    
            return creds
            
        except Exception as e:
            logger.warning(f"Erro ao carregar credenciais: {e}")
            return None
    
    def _save_credentials(self, creds: Credentials):
        """
        Salva credenciais.
        
        Args:
            creds: Credenciais para salvar
        """
        try:
            with open(self.token_path, "wb") as token:
                pickle.dump(creds, token)
        except Exception as e:
            logger.error(f"Erro ao salvar credenciais: {e}")
    
    def authenticate(self, credentials_path: Optional[Path] = None) -> Credentials:
        """
        Autentica com o YouTube.
        
        Args:
            credentials_path: Caminho para arquivo de credenciais
            
        Returns:
            Credenciais autenticadas
            
        Raises:
            DownloadError: Se falhar autenticação
        """
        try:
            # Tenta carregar credenciais salvas
            creds = self._load_credentials()
            if creds:
                return creds
            
            # Usa arquivo de credenciais fornecido ou padrão
            credentials_path = credentials_path or self.credentials_path
            if not credentials_path.exists():
                raise DownloadError(
                    f"Arquivo de credenciais não encontrado: {credentials_path}"
                )
            
            # Inicia fluxo de autenticação
            flow = InstalledAppFlow.from_client_secrets_file(
                str(credentials_path),
                self.SCOPES
            )
            creds = flow.run_local_server(port=0)
            
            # Salva credenciais
            self._save_credentials(creds)
            
            return creds
            
        except Exception as e:
            raise DownloadError(f"Erro na autenticação: {e}")
    
    def build_service(self, credentials_path: Optional[Path] = None):
        """
        Cria serviço autenticado.
        
        Args:
            credentials_path: Caminho para arquivo de credenciais
            
        Returns:
            Serviço do YouTube
            
        Raises:
            DownloadError: Se falhar autenticação
        """
        creds = self.authenticate(credentials_path)
        return build("youtube", "v3", credentials=creds)
    
    def revoke(self):
        """Remove credenciais salvas."""
        if self.token_path.exists():
            try:
                self.token_path.unlink()
                logger.info("Credenciais removidas")
            except Exception as e:
                logger.error(f"Erro ao remover credenciais: {e}")
    
    @staticmethod
    def create_credentials_file(
        client_id: str,
        client_secret: str,
        output_path: Path
    ):
        """
        Cria arquivo de credenciais.
        
        Args:
            client_id: Client ID do projeto
            client_secret: Client secret do projeto
            output_path: Caminho para salvar
        """
        credentials = {
            "installed": {
                "client_id": client_id,
                "project_id": "youtube-shorts-generator",
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": 
                    "https://www.googleapis.com/oauth2/v1/certs",
                "client_secret": client_secret,
                "redirect_uris": ["urn:ietf:wg:oauth:2.0:oob", "http://localhost"]
            }
        }
        
        with open(output_path, "w") as f:
            json.dump(credentials, f, indent=2)
