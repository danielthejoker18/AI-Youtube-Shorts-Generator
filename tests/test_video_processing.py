import os
from Components.yt_dlp_downloader import YtDlpDownloader
from Components.video_manager import VideoManager
from Components.logger import get_logger

logger = get_logger(__name__)

def main():
    # Inicializar gerenciadores
    downloader = YtDlpDownloader()
    video_manager = VideoManager()
    
    # Primeiro, escanear diretório por vídeos não processados
    logger.info("Escaneando diretório por vídeos não processados...")
    video_manager.scan_videos_directory()
    
    # Verificar se há vídeos não processados
    unprocessed = video_manager.get_unprocessed_video()
    if unprocessed:
        logger.info(f"Encontrado vídeo não processado: {unprocessed.title}")
        # Aqui você pode adicionar a lógica de processamento
        # Por enquanto, vamos apenas marcar como processado
        video_manager.mark_as_processed(unprocessed.video_id)
        logger.info("Vídeo marcado como processado")
    else:
        logger.info("Nenhum vídeo não processado encontrado")
        
        # Tentar baixar um novo vídeo
        logger.info("Procurando vídeo viral para baixar...")
        viral_video = downloader.find_viral_video()
        
        if viral_video:
            logger.info(f"Encontrado vídeo viral: {viral_video['title']}")
            
            # Baixar o vídeo
            output_path = downloader.download_video(viral_video['url'])
            
            if output_path:
                # Adicionar ao gerenciador de vídeos
                video_manager.add_video(
                    video_id=viral_video['id'],
                    title=viral_video['title'],
                    path=output_path,
                    url=viral_video['url']
                )
                logger.info(f"Vídeo baixado e adicionado ao banco de dados: {output_path}")
            else:
                logger.error("Falha ao baixar o vídeo")
        else:
            logger.error("Nenhum vídeo viral encontrado")

if __name__ == "__main__":
    main()
