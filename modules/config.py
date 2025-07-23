import json
import yaml
from typing import Dict, Any, List

def load_cfg():
    """Carrega as configurações do arquivo config.json ou config.yaml"""
    try:
        # Tenta carregar JSON primeiro
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        # Fallback para YAML (compatibilidade)
        try:
            with open("config.yaml", "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            raise FileNotFoundError("Nenhum arquivo de configuração encontrado (config.json ou config.yaml)")

def merge_configurations(pattern_config: Dict[str, Any], video_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Faz merge entre pattern_video_configuration e video_configuration.
    Se video_config tem pattern_video_configuration: true, usa apenas o padrão.
    Caso contrário, faz merge das configurações específicas com o padrão.
    """
    if video_config.get("pattern_video_configuration") is True:
        # Usa apenas as configurações padrão
        return pattern_config.copy()
    
    # Faz merge das configurações
    merged_config = pattern_config.copy()
    
    # Sobrescreve com configurações específicas do vídeo
    for key, value in video_config.items():
        if key != "input_url" and key != "pattern_video_configuration":
            merged_config[key] = value
    
    return merged_config

def process_payload_config(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Processa o payload completo e retorna lista de configurações para cada vídeo.
    Cada item da lista contém a configuração completa para processar um vídeo.
    """
    pattern_config = payload.get("pattern_video_configuration", {})
    video_configs = payload.get("video_configuration", [])
    system_config = payload.get("system_configuration", {})
    
    processed_configs = []
    
    for video_config in video_configs:
        # Faz merge das configurações
        merged_video_config = merge_configurations(pattern_config, video_config)
        
        # Adiciona configurações do sistema
        final_config = {
            **system_config,
            **merged_video_config,
            "input_url": video_config["input_url"]
        }
        
        processed_configs.append(final_config)
    
    return processed_configs

def get_system_configuration(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Retorna apenas as configurações do sistema"""
    return payload.get("system_configuration", {}) 