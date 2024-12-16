from Components.youtube_scraper import YouTubeScraper
import logging
from datetime import datetime
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_results_to_file(videos, filename):
    """Save video results to a text file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"YouTube Viral Videos Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, video in enumerate(videos, 1):
            f.write(f"Video {i}:\n")
            f.write(f"Título: {video['title']}\n")
            f.write(f"URL: {video['url']}\n")
            f.write(f"Visualizações: {video['views']:,}\n")
            f.write(f"Duração: {video['duration']}\n")
            f.write("-" * 80 + "\n\n")

def test_scraper():
    try:
        # Criar diretório para resultados se não existir
        results_dir = "results"
        os.makedirs(results_dir, exist_ok=True)
        
        # Nome do arquivo de resultados
        results_file = os.path.join(results_dir, f"viral_videos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
        logger.info("Iniciando busca por vídeos virais...")
        scraper = YouTubeScraper()
        
        # Buscar vídeos em tendência de diferentes regiões
        all_videos = []
        regions = ['US', 'GB', 'CA', 'AU']
        
        for region in regions:
            logger.info(f"Buscando vídeos da região: {region}")
            videos = scraper.get_trending_videos(region=region, max_results=5)
            all_videos.extend(videos)
        
        # Filtrar vídeos por duração (entre 5 e 20 minutos)
        suitable_videos = []
        for video in all_videos:
            duration_seconds = scraper._duration_to_seconds(video['duration'])
            if 300 <= duration_seconds <= 1200:  # entre 5 e 20 minutos
                suitable_videos.append(video)
        
        if suitable_videos:
            # Salvar resultados no arquivo
            save_results_to_file(suitable_videos, results_file)
            logger.info(f"Resultados salvos em: {results_file}")
            logger.info(f"Total de vídeos encontrados: {len(suitable_videos)}")
        else:
            logger.error("Nenhum vídeo adequado encontrado")
            
    except Exception as e:
        logger.error(f"Erro durante o teste: {str(e)}")

if __name__ == "__main__":
    test_scraper()
