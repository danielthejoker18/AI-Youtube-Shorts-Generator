import os
import json
import time
import webbrowser
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from pytubefix import YouTube
from .logger import get_logger

logger = get_logger(__name__)

class YouTubeAuth:
    def __init__(self, cookies_file: str = "youtube.cookies", token_file: str = "youtube.token"):
        """
        Initialize YouTube authentication manager.
        
        Args:
            cookies_file: Path to save cookies
            token_file: Path to save OAuth token
        """
        self.cookies_file = Path(cookies_file)
        self.token_file = Path(token_file)
        self._last_auth_check = None
        self._auth_valid = False
        
    def is_authenticated(self, force_check: bool = False) -> bool:
        """
        Check if we have valid authentication.
        
        Args:
            force_check: If True, ignores cached result and checks again
            
        Returns:
            bool: True if authenticated, False otherwise
        """
        # Se já verificamos nos últimos 5 minutos e não foi forçado, retorna o último resultado
        if not force_check and self._last_auth_check:
            if datetime.now() - self._last_auth_check < timedelta(minutes=5):
                return self._auth_valid
                
        # Verifica se os arquivos existem
        if not (self.cookies_file.exists() and self.token_file.exists()):
            logger.warning("Authentication files not found")
            self._update_auth_status(False)
            return False
            
        # Testa a autenticação com um vídeo restrito
        try:
            test_url = "https://www.youtube.com/watch?v=54dabgZJ5YA"  # The Witcher 4 trailer (age-restricted)
            yt = YouTube(test_url, use_oauth=True, allow_oauth_cache=True)
            
            # Tenta acessar informações do vídeo
            title = yt.title
            stream = yt.streams.first()
            
            if not stream:
                raise Exception("Could not access video streams")
                
            logger.debug(f"Successfully accessed age-restricted video: {title}")
            self._update_auth_status(True)
            return True
            
        except Exception as e:
            logger.warning(f"Authentication test failed: {e}")
            self._update_auth_status(False)
            return False
            
    def _update_auth_status(self, status: bool):
        """Update authentication status and timestamp"""
        self._auth_valid = status
        self._last_auth_check = datetime.now()
        
    def authenticate(self) -> bool:
        """
        Perform YouTube authentication.
        This will open a browser window for the user to log in.
        
        Returns:
            bool: True if authentication successful, False otherwise
        """
        try:
            logger.info("Starting YouTube authentication process...")
            logger.info("This will open a browser window. Please:")
            logger.info("1. Log in with your YouTube account")
            logger.info("2. Accept the permissions request")
            logger.info("3. Return here after logging in")
            
            # Abre o navegador com a URL de autenticação
            auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
            auth_url += "?client_id=861556708454-d6dlm3lh05idd8npek18k6be8ba3oc68.apps.googleusercontent.com"
            auth_url += "&redirect_uri=http://localhost:8080"
            auth_url += "&response_type=code"
            auth_url += "&scope=https://www.googleapis.com/auth/youtube.force-ssl"
            auth_url += "&access_type=offline"
            
            webbrowser.open(auth_url)
            
            # Espera um pouco para o usuário fazer login
            time.sleep(5)
            
            # Inicia o processo de autenticação do pytubefix
            yt = YouTube(
                "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                use_oauth=True,
                allow_oauth_cache=True
            )
            
            # Espera um pouco para a autenticação completar
            time.sleep(2)
            
            # Testa a autenticação
            if self.is_authenticated(force_check=True):
                logger.info("Authentication successful!")
                logger.info("You can now close the browser window")
                return True
            else:
                logger.error("Authentication failed verification")
                return False
                
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return False
            
    def clear_auth(self):
        """Remove all authentication files"""
        try:
            if self.cookies_file.exists():
                self.cookies_file.unlink()
            if self.token_file.exists():
                self.token_file.unlink()
            self._update_auth_status(False)
            logger.info("Authentication files cleared")
        except Exception as e:
            logger.error(f"Error clearing auth files: {e}")
            
    def ensure_authenticated(self) -> bool:
        """
        Ensure we have valid authentication, attempting to authenticate if needed.
        
        Returns:
            bool: True if authenticated (either already or after new auth), False if failed
        """
        if self.is_authenticated():
            return True
            
        logger.info("No valid authentication found, starting new authentication...")
        return self.authenticate()
        
def setup_auth():
    """
    Função auxiliar para configurar a autenticação pela primeira vez.
    """
    auth = YouTubeAuth()
    
    if auth.ensure_authenticated():
        logger.info("YouTube authentication setup complete!")
        logger.info("You can now run main.py to download age-restricted videos")
        return True
    else:
        logger.error("YouTube authentication setup failed")
        logger.error("Please try again and make sure to:")
        logger.error("1. Log in with your YouTube account")
        logger.error("2. Accept any necessary permissions")
        logger.error("3. Make sure your account is age-verified")
        return False
        
if __name__ == "__main__":
    setup_auth()
