# Podcast Cuts

Sistema automatizado para criar e publicar cortes de podcasts no YouTube, utilizando IA para selecionar os melhores momentos e gerar miniaturas personalizadas.

## Funcionalidades

- Download automático de vídeos do YouTube
- Transcrição de áudio usando Whisper
- Seleção inteligente de highlights usando GPT-4
- Geração de miniaturas personalizadas com DALL-E
- Edição automática de vídeos para formato vertical (Shorts)
- Upload automático para YouTube

## Requisitos

### Sistema
- Python 3.9 ou superior
- Poetry (gerenciador de dependências)
- FFmpeg
- ImageMagick 7.1.1 ou superior

### APIs e Credenciais
- OpenAI API Key (para GPT-4 e DALL-E)
- Credenciais do YouTube API

## Instalação

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd podcast-cuts
```

2. Instale o Poetry (se ainda não tiver):
```bash
# Windows (PowerShell)
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Linux/macOS
curl -sSL https://install.python-poetry.org | python3 -
```

3. Instale as dependências Python:
```bash
poetry install
```

4. Instale o ImageMagick:
```bash
# Windows
python install_imagemagick.py

# Linux
sudo apt-get install imagemagick

# macOS
brew install imagemagick
```

5. Configure as credenciais:

Crie um arquivo `.env` na raiz do projeto com:
```
OPENAI_API_KEY=sua_chave_api_openai
```

Para o YouTube, você precisa:
1. Criar um projeto no Google Cloud Console
2. Habilitar a YouTube Data API v3
3. Criar credenciais OAuth 2.0
4. Baixar o arquivo `client_secret.json` e colocá-lo na raiz do projeto

## Configuração

As configurações do projeto podem ser ajustadas no arquivo `config.yaml`:

```yaml
paths:
  raw: raw          # Pasta para vídeos originais
  clips: clips      # Pasta para os cortes gerados
whisper_size: base  # Tamanho do modelo de transcrição (tiny/base/small/medium)
highlights: 3       # Número de cortes por episódio
tags: ["podcast", "cortes", "clipverso"]
test_mode: true     # true = pula upload para YouTube

openai_models:
  highlighter: gpt-4o
  editor: gpt-4o
  thumbnail: dall-e-3
```

## Uso

1. Coloque a URL do podcast no arquivo `input_url.txt` ou use como argumento:
```bash
poetry run python main.py "URL_DO_PODCAST"
```

2. O sistema irá:
   - Baixar o vídeo
   - Transcrever o áudio
   - Selecionar os melhores momentos
   - Gerar miniaturas
   - Criar os cortes
   - Fazer upload para o YouTube (se test_mode = false)

## Estrutura de Diretórios

```
podcast-cuts/
├── clips/          # Cortes gerados
├── raw/           # Vídeos originais
├── logs/          # Logs de erros e custos
├── modules/       # Módulos do sistema
├── fonts/         # Fontes para legendas
├── config.yaml    # Configurações
├── .env           # Variáveis de ambiente
└── main.py        # Script principal
```

## Logs e Monitoramento

- `logs/erros.log`: Registra erros durante o processamento
- `logs/custos.log`: Registra custos de uso da API OpenAI

## Dependências Principais

- yt-dlp: Download de vídeos
- faster-whisper: Transcrição de áudio
- moviepy: Edição de vídeo
- openai: Integração com GPT-4 e DALL-E
- google-api-python-client: Upload para YouTube
- pillow: Processamento de imagens
- opencv-python: Processamento de vídeo

## Solução de Problemas

1. Erro no ImageMagick:
   - Verifique se o caminho no `moviepy_config.py` está correto
   - Execute `python install_imagemagick.py` novamente

2. Erro na API do YouTube:
   - Verifique se o `client_secret.json` está presente
   - Confirme se as credenciais têm permissão para upload

3. Erro na API OpenAI:
   - Verifique se a chave API está correta no `.env`
   - Confirme se tem créditos suficientes

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 