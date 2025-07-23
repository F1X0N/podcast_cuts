import os
import json
import yaml
import requests
from openai import OpenAI
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

LOG_DIR = "logs"
COST_LOG = os.path.join(LOG_DIR, "custos.log")
ERROR_LOG = os.path.join(LOG_DIR, "erros.log")
os.makedirs(LOG_DIR, exist_ok=True)

# Carrega configuração (JSON ou YAML como fallback)
def load_config():
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

# Carrega configuração global
CONFIG = load_config()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Tabela de preços OpenAI (USD por 1k tokens)
# Atualize conforme necessário
OPENAI_PRICES = {
    "gpt-4o": {"input": 5.0/1_000_000, "output": 15.0/1_000_000},
    "o3": {"input": 0.15/1_000_000, "output": 0.6/1_000_000},  # GPT-4o-mini
    "gpt-4-turbo": {"input": 10.0/1_000_000, "output": 30.0/1_000_000},
    "gpt-4": {"input": 30.0/1_000_000, "output": 60.0/1_000_000},
    "gpt-3.5-turbo": {"input": 0.5/1_000_000, "output": 1.5/1_000_000},
    "dall-e-3": {"image": 0.04},
    "dall-e-2": {"image": 0.02},
}

# Armazena estatísticas de uso
LLM_STATS = {}

# Função para buscar cotação do dólar (exchangerate.host)
def get_usd_brl():
    try:
        resp = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=BRL")
        return resp.json()["rates"]["BRL"]
    except Exception:
        return None

# Função para salvar log de custos por episódio
def save_cost_log(episode_url=None):
    usd_brl = get_usd_brl() or 5.0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_usd = sum(s["usd"] for s in LLM_STATS.values())
    total_brl = total_usd * usd_brl
    log = {
        "data": now,
        "episodio": episode_url,
        "usd_brl": usd_brl,
        "total_usd": total_usd,
        "total_brl": total_brl,
        "etapas": LLM_STATS.copy()
    }
    with open(COST_LOG, "a", encoding="utf-8") as f:
        f.write(yaml.dump([log], allow_unicode=True))

# Função para salvar log de erro
def save_error_log(error, episode_url=None):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ERROR_LOG, "a", encoding="utf-8") as f:
        f.write(f"[{now}] Episódio: {episode_url}\n{error}\n{'-'*60}\n")

# Função centralizada para chamada de LLM
def call_llm(role, messages=None, prompt=None, image=False, n=1, size=None, quality=None, response_format=None):
    """
    role: etapa do pipeline (ex: 'highlighter', 'editor', 'thumbnail')
    messages: lista de mensagens para chat/completion
    prompt: prompt para geração de imagem
    image: se True, gera imagem
    n, size, quality: parâmetros para imagem
    response_format: formato de resposta esperado (ex: {"type": "json_object"})
    """
    # Obtém modelo da configuração do sistema
    system_config = CONFIG.get("system_configuration", {})
    openai_models = system_config.get("openai_models", {})
    model = openai_models.get(role, "gpt-4o")  # Fallback para gpt-4o
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    stats = LLM_STATS.setdefault(role, {"input": 0, "output": 0, "cache": 0, "usd": 0, "calls": 0})
    result = None
    if image:
        # Geração de imagem
        response = client.images.generate(
            model=model,
            prompt=prompt,
            n=n,
            size=size or "1024x1024",
            quality=quality or "standard"
        )
        stats["usd"] += OPENAI_PRICES[model]["image"] * n
        result = response
    else:
        # Chat/completion
        kwargs = {
            "model": model,
            "messages": messages,
        }
        if response_format:
            kwargs["response_format"] = response_format
            
        response = client.chat.completions.create(**kwargs)
        usage = response.usage
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
        stats["input"] += input_tokens
        stats["output"] += output_tokens
        stats["usd"] += (
            input_tokens * OPENAI_PRICES[model]["input"] +
            output_tokens * OPENAI_PRICES[model]["output"]
        )
        result = response
    stats["calls"] += 1
    return result

# Função para exibir relatório final
def print_llm_report():
    usd_brl = get_usd_brl() or 5.0
    print("\n===== RELATÓRIO DE USO DE LLM =====")
    total_usd = 0
    for etapa, s in LLM_STATS.items():
        print(f"\nEtapa: {etapa}")
        print(f"  Tokens de entrada: {s['input']}")
        print(f"  Tokens de saída: {s['output']}")
        print(f"  Chamadas: {s['calls']}")
        print(f"  Custo em dólar: US$ {s['usd']:.4f}")
        print(f"  Custo em real: R$ {s['usd']*usd_brl:.4f}")
        total_usd += s["usd"]
    print(f"\nCUSTO TOTAL: US$ {total_usd:.4f} | R$ {total_usd*usd_brl:.4f}")
    print("===================================\n") 