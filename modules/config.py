import yaml

def load_cfg():
    """Carrega as configurações do arquivo config.yaml"""
    with open("config.yaml", "r") as f:
        return yaml.safe_load(f) 