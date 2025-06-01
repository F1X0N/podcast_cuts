# Podcast Cuts

Sistema automatizado para criar e publicar cortes de podcasts no YouTube.

## Requisitos

- Python 3.9 ou superior
- Poetry (gerenciador de dependências)
- Credenciais do YouTube API

## Instalação

1. Instale o Poetry (se ainda não tiver):
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2. Clone o repositório:
```bash
git clone <seu-repositorio>
cd podcast-cuts
```

3. Instale as dependências:
```bash
poetry install
```

4. Configure as credenciais do YouTube:
Crie um arquivo `.env` na raiz do projeto com:
```
YOUTUBE_CLIENT_ID=seu_client_id
YOUTUBE_CLIENT_SECRET=seu_client_secret
YOUTUBE_REFRESH_TOKEN=seu_refresh_token
```

## Uso

Para processar um episódio de podcast:
```bash
poetry run python main.py "URL_DO_PODCAST"
```

## Configuração

As configurações do projeto podem ser ajustadas no arquivo `config.yaml`:
- `whisper_size`: Tamanho do modelo de transcrição (tiny/base/small/medium)
- `highlights`: Número de cortes por episódio
- `tags`: Tags padrão para os vídeos do YouTube 