import os
from pathlib import Path
from dotenv import load_dotenv
from Components.video_manager import VideoManager
from Components.Transcription import Transcriber
from Components.highlight_detector import HighlightDetector
from Components.logger import get_logger
from Components.video_processor import VideoProcessor

# Carrega variáveis de ambiente
load_dotenv()

# Limpa logs antigos
def clean_logs():
    """Limpa arquivos de log antigos"""
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in logs_dir.glob("*.log"):
            try:
                log_file.unlink()
            except Exception as e:
                print(f"Error deleting log file {log_file}: {e}")
    logs_dir.mkdir(exist_ok=True)


# Configura logger
logger = get_logger(__name__)

def process_video(video_path: str, video_id: str) -> bool:
    """
    Process a complete video: transcription, highlight detection and cutting.
    
    Args:
        video_path: Path to video file
        video_id: Video ID
        
    Returns:
        bool: True if processed successfully, False otherwise
    """
    try:
        # Verifica se o arquivo existe
        if not os.path.exists(video_path):
            logger.error(f"Arquivo de vídeo não encontrado: {video_path}")
            return False
            
        # Initialize components
        transcriber = Transcriber()
        highlight_detector = HighlightDetector()
        
        # Cria diretório de saída
        output_dir = os.path.join("results", video_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Inicializa processador de vídeo com o caminho do vídeo
        video_processor = VideoProcessor(
            video_path=video_path,
            output_dir=output_dir
        )
        
        # Try to get transcription
        logger.info(f"Obtendo transcrição para o vídeo {video_id}")
        result = transcriber.transcribe(video_path, video_id)
        
        if not result:
            logger.error("Falha ao obter transcrição")
            return False
            
        # Format transcription for highlight detection
        transcription = {
            'text': result['text'],
            'segments': [{
                'text': segment['text'],
                'start': segment['start'],
                'end': segment['end']
            } for segment in result['segments']],
            'language': result['language']
        }
            
        # Detect highlights
        logger.info("Detectando highlights")
        highlights = highlight_detector.detect_highlights(
            transcription['text'],
            transcription['segments']
        )
        
        if not highlights:
            logger.warning("Nenhum highlight encontrado")
            return False
            
        # Define output path
        output_path = os.path.join(output_dir, f"shorts_{video_id}.mp4")
            
        # Process the video
        logger.info("Processando segmentos do vídeo")
        video_processor.process_video_segments(highlights, output_path)
        
        logger.info("Vídeo processado com sucesso")
        return True
        
    except Exception as e:
        logger.error(f"Erro processando vídeo: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def main():
    try:
        # Initialize video manager
        video_manager = VideoManager()
        
        # Primeiro verifica vídeos locais não processados
        unprocessed_videos = video_manager.get_unprocessed_videos()
        
        if not unprocessed_videos:
            logger.info("Nenhum vídeo local para processar, buscando novos vídeos do YouTube...")
            
            # Inicializa YouTube scraper
            from Components.youtube_scraper import YouTubeScraper
            scraper = YouTubeScraper()
            
            try:
                # Busca novos vídeos
                new_videos = scraper.fetch_new_videos()
                
                if not new_videos:
                    logger.info("Nenhum vídeo novo encontrado no YouTube")
                    return
                    
                logger.info(f"Encontrados {len(new_videos)} novos vídeos no YouTube")
                
                # Baixa os vídeos
                for video in new_videos:
                    try:
                        video_path = scraper.download_video(video['url'])
                        if video_path:
                            video_manager.add_video(
                                video_id=video['id'],
                                title=video['title'],
                                path=video_path,
                                url=video['url'],
                                duration=video.get('duration')
                            )
                    except Exception as e:
                        logger.error(f"Erro baixando vídeo {video['id']}: {str(e)}")
                        continue
                
                # Atualiza lista de vídeos não processados
                unprocessed_videos = video_manager.get_unprocessed_videos()
                
                if not unprocessed_videos:
                    logger.info("Nenhum vídeo disponível para processar após download")
                    return
                    
            except Exception as e:
                logger.error(f"Erro buscando vídeos do YouTube: {str(e)}")
                return
        
        logger.info(f"Encontrados {len(unprocessed_videos)} vídeos para processar")
        
        # Processa cada vídeo
        for video_path, video_id in unprocessed_videos:
            try:
                logger.info(f"\nProcessando vídeo: {video_id}")
                success = process_video(video_path, video_id)
                if success:
                    video_manager.mark_as_processed(video_id)
                else:
                    video_manager.mark_as_processed(video_id, error="Falha no processamento")
            except Exception as e:
                logger.error(f"Erro processando vídeo {video_id}: {str(e)}")
                video_manager.mark_as_processed(video_id, error=str(e))
                continue
                
    except Exception as e:
        logger.error(f"Erro no processo principal: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    main()