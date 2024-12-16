"""
Script para testar o pipeline completo do projeto.

Este script testa o pipeline completo de processamento de vídeos, incluindo:
1. Download de vídeos do YouTube
2. Processamento de áudio e vídeo
3. Geração de shorts com base em highlights
"""

import os
from typing import Dict
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

from Components.media.pipeline import VideoPipeline, PipelineConfig
from Components.media.video_downloader import VideoDownloader
from Components.core.logger import ComponentLogger

# Setup logger
logger = ComponentLogger(__name__)

# Load environment variables
load_dotenv()

def format_size(size_bytes: int) -> str:
    """
    Format bytes size to human readable format.
    
    Args:
        size_bytes (int): Size in bytes
        
    Returns:
        str: Formatted size string (e.g., "1.5MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}GB"

def format_duration(seconds: int) -> str:
    """
    Format seconds to HH:MM:SS.
    
    Args:
        seconds (int): Duration in seconds
        
    Returns:
        str: Formatted duration string
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = seconds % 60
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"

def print_video_info(video_info: Dict) -> None:
    """
    Print video information in a formatted way.
    
    Args:
        video_info (Dict): Dictionary containing video information
    """
    print("\nVídeo selecionado:")
    print("=" * 50)
    print(f"Título: {video_info['title']}")
    print(f"Duração: {format_duration(video_info['duration'])}")
    print(f"Views: {video_info['views']:,}")
    print(f"URL: {video_info['url']}")
    print("=" * 50)

def test_pipeline() -> None:
    """Run the complete video processing pipeline test."""
    try:
        # 1. Initialize components
        downloader = VideoDownloader()
        
        # 2. Configure pipeline
        config = PipelineConfig(
            min_highlight_duration=15.0,
            max_highlight_duration=60.0,
            min_highlight_score=0.7,
            detect_faces=True,
            clean_audio=True,
            normalize_volume=True,
            add_subtitles=True,
            add_transitions=True,
            add_zoom=True
        )
        
        pipeline = VideoPipeline(
            config=config,
            output_dir=Path("shorts")
        )

        # 3. Get video URL and info
        video_url = input("\nDigite a URL do vídeo do YouTube: ").strip()
        if not video_url:
            logger.error("❌ URL inválida")
            return

        # Get video info first
        try:
            video_info = downloader.get_info(video_url)
            print_video_info(video_info)
        except Exception as e:
            logger.error(f"❌ Erro ao obter informações do vídeo: {str(e)}")
            return

        # 4. Download video
        logger.info("\n⬇️ Downloading video...")
        try:
            video_path = downloader.download(video_url)
        except Exception as e:
            logger.error(f"❌ Erro ao baixar vídeo: {str(e)}")
            return

        # 5. Process video
        logger.info("\n🎬 Processing video...")
        try:
            short_path = pipeline.process_video(video_path)
            logger.info(f"\n✅ Short gerado com sucesso: {short_path}")
        except Exception as e:
            logger.error(f"❌ Erro ao processar vídeo: {str(e)}")
            return
        
    except KeyboardInterrupt:
        logger.info("\n\n⚠️ Processo interrompido pelo usuário")
    except Exception as e:
        logger.error(f"\n❌ Erro inesperado: {str(e)}")

if __name__ == "__main__":
    print("Iniciando teste do pipeline completo...")
    print("Pressione Ctrl+C a qualquer momento para cancelar")
    print("-" * 50)
    test_pipeline()
