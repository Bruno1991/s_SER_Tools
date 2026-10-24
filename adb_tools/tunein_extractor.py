"""Módulo para interceptação e extração completa de estações de rádio e links de streaming do TuneIn Radio.

Baseado na engenharia reversa do APK tunein.player:
- Protocolo: RadioTime OPML / REST API
- Endpoints: Browse.ashx, Tune.ashx
- Parâmetros: partnerId=xwhZkVKi, render=json
- User-Agent: TuneIn/1.0 (Android)
"""

import concurrent.futures
import json
import logging
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s: %(message)s")
logger = logging.getLogger("TuneInExtractor")

PARTNER_ID = "xwhZkVKi"
BASE_URL = "http://opml.radiotime.com"
USER_AGENT = "TuneIn/1.0 (Android)"
TIMEOUT = 12


def make_request(url: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Executa requisição HTTP com headers e timeout padrão."""
    if params:
        query_str = urllib.parse.urlencode(params)
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}{query_str}"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            raw_data = response.read().decode("utf-8", errors="replace")
            return json.loads(raw_data)
    except Exception as e:
        logger.debug("Falha na requisicao para %s: %s", url, e)
        return None


def resolve_station_stream(station: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve a URL de streaming direto via Tune.ashx."""
    guide_id = station.get("guide_id")
    if not guide_id:
        return station

    tune_url = f"{BASE_URL}/Tune.ashx?id={guide_id}&render=json&partnerId={PARTNER_ID}"
    station["tune_api_url"] = tune_url
    station["direct_stream_url"] = None
    station["stream_media_type"] = None
    station["stream_bitrate"] = None
    station["stream_reliability"] = None
    station["all_streams"] = []

    res = make_request(tune_url)
    if not res:
        return station

    body = res.get("body", [])
    if isinstance(body, list):
        for stream in body:
            stream_url = stream.get("url")
            if stream_url:
                stream_info = {
                    "url": stream_url,
                    "media_type": stream.get("media_type"),
                    "bitrate": stream.get("bitrate"),
                    "reliability": stream.get("reliability"),
                    "is_direct": stream.get("is_direct", False),
                }
                station["all_streams"].append(stream_info)
                if not station["direct_stream_url"]:
                    station["direct_stream_url"] = stream_url
                    station["stream_media_type"] = stream.get("media_type")
                    station["stream_bitrate"] = stream.get("bitrate")
                    station["stream_reliability"] = stream.get("reliability")

    return station


class TuneInRadioExtractor:
    """Extrator avançado de estações de rádio e streams do TuneIn."""

    def __init__(self, partner_id: str = PARTNER_ID, max_workers: int = 25):
        self.partner_id = partner_id
        self.max_workers = max_workers
        self.stations: Dict[str, Dict[str, Any]] = {}
        self.visited_urls: Set[str] = set()

    def _extract_outlines(self, items: List[Dict[str, Any]], category_name: str, queue: List[Dict[str, str]]):
        """Processa outlines do payload OPML recursivamente."""
        for item in items:
            element = item.get("element", "")
            item_type = item.get("type", "")
            text = item.get("text", "")
            guide_id = item.get("guide_id")
            url = item.get("URL")

            # Estação de áudio
            if item_type == "audio" or (guide_id and guide_id.startswith("s")):
                if guide_id and guide_id not in self.stations:
                    self.stations[guide_id] = {
                        "guide_id": guide_id,
                        "name": text,
                        "subtext": item.get("subtext", ""),
                        "category": category_name,
                        "genre_id": item.get("genre_id"),
                        "declared_formats": item.get("formats", ""),
                        "declared_bitrate": item.get("bitrate"),
                        "logo": item.get("image"),
                        "reliability": item.get("reliability"),
                        "item_type": item.get("item", "station"),
                    }

            # Link para navegação interna
            elif item_type == "link" and url:
                if url not in self.visited_urls:
                    sub_cat = f"{category_name} > {text}" if category_name else text
                    queue.append({"url": url, "category": sub_cat})

            # Filhos embutidos
            children = item.get("children", [])
            if children and isinstance(children, list):
                child_cat = f"{category_name} > {text}" if category_name else text
                self._extract_outlines(children, child_cat, queue)

    def crawl_directory(self, target_seeds: List[Dict[str, str]], max_depth: int = 3, max_stations: int = 2500):
        """Navega sistematicamente pelas árvores do diretório TuneIn."""
        queue: List[Dict[str, Any]] = []
        for seed in target_seeds:
            queue.append({"url": seed["url"], "category": seed["category"], "depth": 0})

        logger.info("Iniciando varredura com %d sementes de busca (limite: %d)...", len(queue), max_stations)

        while queue and len(self.stations) < max_stations:
            current = queue.pop(0)
            url = current["url"]
            category = current["category"]
            depth = current["depth"]

            if url in self.visited_urls:
                continue
            self.visited_urls.add(url)

            # Garante render=json e partnerId
            parsed = urllib.parse.urlparse(url)
            params = dict(urllib.parse.parse_qsl(parsed.query))
            params["render"] = "json"
            params["partnerId"] = self.partner_id
            clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

            data = make_request(clean_url, params)
            if not data or "body" not in data:
                continue

            body = data.get("body", [])
            if not isinstance(body, list):
                continue

            next_queue: List[Dict[str, str]] = []
            self._extract_outlines(body, category, next_queue)

            if depth < max_depth and len(self.stations) < max_stations:
                for nxt in next_queue:
                    if nxt["url"] not in self.visited_urls:
                        queue.append({
                            "url": nxt["url"],
                            "category": nxt["category"],
                            "depth": depth + 1
                        })

            if len(self.stations) % 100 == 0 or len(queue) == 0:
                logger.info("Total de rádios catalogadas: %d (fila restante: %d)", len(self.stations), len(queue))

        logger.info("Varredura concluída: %d rádios encontradas.", len(self.stations))

    def resolve_all_streams(self) -> List[Dict[str, Any]]:
        """Resolve links de streaming em paralelo para todas as rádios catalogadas."""
        logger.info("Resolvendo URLs diretas de streaming para %d estações (workers=%d)...", len(self.stations), self.max_workers)
        resolved_list: List[Dict[str, Any]] = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_station = {
                executor.submit(resolve_station_stream, station): station
                for station in self.stations.values()
            }

            completed = 0
            total = len(future_to_station)
            for future in concurrent.futures.as_completed(future_to_station):
                completed += 1
                try:
                    res = future.result()
                    resolved_list.append(res)
                except Exception as e:
                    station = future_to_station[future]
                    logger.warning("Erro ao resolver stream de %s: %s", station.get("guide_id"), e)
                    resolved_list.append(station)

                if completed % 100 == 0 or completed == total:
                    logger.info("Progresso de resolução de streams: %d / %d (%.1f%%)", completed, total, (completed / total) * 100)

        return resolved_list

    def save_to_files(self, stations: List[Dict[str, Any]], target_paths: List[str]) -> Dict[str, Any]:
        """Salva a lista completa em formato JSON nos destinos especificados."""
        # Estatísticas
        streams_found = sum(1 for s in stations if s.get("direct_stream_url"))
        categories = sorted(list(set(s.get("category", "") for s in stations)))

        dataset = {
            "metadata": {
                "extracted_at": datetime.now(timezone.utc).isoformat(),
                "app": "tunein.player",
                "partner_id": self.partner_id,
                "total_stations": len(stations),
                "total_active_streams": streams_found,
                "coverage_percentage": f"{(streams_found / len(stations) * 100):.2f}%" if stations else "0%",
                "categories_count": len(categories),
            },
            "categories": categories,
            "stations": stations,
        }

        for path_str in target_paths:
            path = Path(path_str)
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(dataset, f, ensure_ascii=False, indent=2)
            logger.info("Arquivo gravado com sucesso: %s (%d bytes)", path, path.stat().st_size)

        return dataset


def run_full_extraction(max_stations: int = 1500) -> Dict[str, Any]:
    """Executa o pipeline completo de extração com cobertura expandida."""
    # Sementes completas: Brasil (capitais principais e cidades), Em Alta, Gêneros e Internacional
    seeds = [
        # Principais Capitais e Cidades Brasileiras
        {"url": f"{BASE_URL}/Browse.ashx?id=r100563", "category": "Brasil > São Paulo"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100587", "category": "Brasil > Rio de Janeiro"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100585", "category": "Brasil > Belo Horizonte"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100559", "category": "Brasil > Brasília"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100567", "category": "Brasil > Curitiba"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100580", "category": "Brasil > Porto Alegre"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100561", "category": "Brasil > Salvador"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100574", "category": "Brasil > Fortaleza"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r102235", "category": "Brasil > Recife"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100579", "category": "Brasil > Goiânia"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100562", "category": "Brasil > Florianópolis"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100581", "category": "Brasil > Manaus"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100558", "category": "Brasil > Belém"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100577", "category": "Brasil > Campinas"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100578", "category": "Brasil > Ribeirão Preto"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100576", "category": "Brasil > Santos"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r101223", "category": "Brasil > Geral"},
        # Em Alta & Mais Ouvidas
        {"url": f"{BASE_URL}/Browse.ashx?c=best", "category": "Melhores & Em Alta"},
        {"url": f"{BASE_URL}/Browse.ashx?c=local", "category": "Rádios Locais"},
        # Gêneros Musicais
        {"url": f"{BASE_URL}/Browse.ashx?id=c57951", "category": "Música > Rock"},
        {"url": f"{BASE_URL}/Browse.ashx?id=c57943", "category": "Música > Top 40 & Pop"},
        {"url": f"{BASE_URL}/Browse.ashx?id=c100002533", "category": "Música > Latina & Brasileira"},
        {"url": f"{BASE_URL}/Browse.ashx?id=c57944", "category": "Música > Jazz"},
        {"url": f"{BASE_URL}/Browse.ashx?id=c57942", "category": "Música > Hip Hop"},
        {"url": f"{BASE_URL}/Browse.ashx?id=c57940", "category": "Música > Country"},
        {"url": f"{BASE_URL}/Browse.ashx?id=c100000949", "category": "Música > Reggae & Dancehall"},
        {"url": f"{BASE_URL}/Browse.ashx?id=c1367173", "category": "Música > Soul & R&B"},
        # Notícias e Esportes
        {"url": f"{BASE_URL}/Browse.ashx?c=talk", "category": "Notícias & Conversa"},
        {"url": f"{BASE_URL}/Browse.ashx?c=sports", "category": "Esportes"},
        # América do Sul e Europa
        {"url": f"{BASE_URL}/Browse.ashx?id=r100294", "category": "Internacional > Argentina"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r100325", "category": "Internacional > Colômbia"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r101229", "category": "Internacional > Chile"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r101217", "category": "Internacional > Europa"},
        {"url": f"{BASE_URL}/Browse.ashx?id=r101218", "category": "Internacional > América do Norte"},
    ]

    extractor = TuneInRadioExtractor(partner_id=PARTNER_ID, max_workers=30)
    extractor.crawl_directory(seeds, max_depth=3, max_stations=max_stations)
    resolved_stations = extractor.resolve_all_streams()

    output_files = [
        r"C:\dev\s_ADB_Tools\decompiled_sources\tunein_radio_links.json",
        r"C:\dev\s_ADB_Tools\decompiled_sources\tunein.player\radio_links.json",
        r"C:\dev\s_ADB_Tools\extracted_apks\tunein.player\tunein_radio_links.json",
    ]

    result = extractor.save_to_files(resolved_stations, output_files)
    return result


if __name__ == "__main__":
    count = 1500
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            pass
    run_full_extraction(max_stations=count)
