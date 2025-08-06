# Podcast Cuts

Sistema automatizado para criar e publicar cortes de podcasts no YouTube, utilizando IA para selecionar os melhores momentos e gerar miniaturas personalizadas.

## Funcionalidades

- Download automático de vídeos do YouTube
- Transcrição de áudio usando Whisper
- Seleção inteligente de highlights usando GPT-4
- Geração de miniaturas personalizadas com DALL-E
- Edição automática de vídeos para formato vertical (Shorts)
- Upload automático para YouTube
- Sistema de checkpoints para retomada de processamento
- Processamento em lote de múltiplos vídeos
- **Template dinâmico** que se adapta ao formato do vídeo
- **Controle de recorte** (fit/center) para diferentes estilos
- **Posicionamento inteligente** de elementos visuais
- **Legendas dinâmicas** com estilo profissional (fonte Anton, amarelo, contorno preto)

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

**Exemplo de configuração do YouTube:**
O arquivo `client_secret.example.json` mostra a estrutura necessária. Copie-o para `client_secret.json` e preencha com suas credenciais reais.

## Configuração

As configurações do projeto são definidas no arquivo `config.json`:

```json
{
    "pattern_video_configuration": {
        "tags": ["cortes", "fy", "foryou", "clipverso-ofc"],
        "highlights": 1,
        "append_outro": true,
        "content_speed": 1.25,
        "preserve_pitch": true,
        "video_duration": 61
    },
    "video_configuration": [
        {
            "input_url": "https://www.youtube.com/watch?v=VIDEO_ID",
            "tags": ["cortes", "clipverso", "foryou"],
            "highlights": 1,
            "append_outro": true,
            "content_speed": 1.25,
            "preserve_pitch": true,
            "video_duration": 61
        },
        {
            "input_url": "https://www.youtube.com/watch?v=OUTRO_VIDEO_ID",
            "pattern_video_configuration": true
        }
    ],
    "system_configuration": {
        "upload_mode": false,
        "upload_delay": {
            "min_seconds": 1800,
            "max_seconds": 3600
        },
        "video_optimization": {
            "use_gpu": true,
            "quality": "balanced",
            "enable_parallel": true
        },
        "paths": {
            "raw": "raw",
            "clips": "clips"
        },
        "whisper_size": "base",
        "openai_models": {
            "highlighter": "o3",
            "editor": "o3",
            "thumbnail": "dall-e-3"
        }
    }
}
```

### Estrutura da Configuração

#### `pattern_video_configuration`
Configurações padrão aplicadas a todos os vídeos:
- **tags**: Tags padrão para todos os cortes
- **highlights**: Número de cortes por episódio
- **append_outro**: Se deve anexar outro ao final
- **content_speed**: Velocidade do conteúdo (1.25 = 25% mais rápido)
- **preserve_pitch**: Manter tom da voz original
- **video_duration**: Duração final em segundos
- **crop_mode**: Modo de recorte ("fit" ou "center")

#### `video_configuration`
Lista de vídeos para processar:
- **input_url**: URL do vídeo do YouTube
- **pattern_video_configuration**: `true` para usar apenas configurações padrão
- Outras configurações específicas sobrescrevem o padrão

#### `system_configuration`
Configurações do sistema:
- **upload_mode**: `true` para fazer upload real, `false` para simular
- **upload_delay**: Delay entre uploads (em segundos)
- **video_optimization**: Configurações de otimização
- **paths**: Diretórios de trabalho
- **whisper_size**: Tamanho do modelo Whisper
- **openai_models**: Modelos OpenAI a usar

### ⚡ Configurações de Velocidade

O sistema permite controlar a velocidade do conteúdo principal dos shorts:

- **content_speed**: Velocidade do conteúdo (padrão: 1.25x = 25% mais rápido)
  - `1.0` = velocidade normal
  - `1.25` = 25% mais rápido (padrão recomendado)
  - `1.5` = 50% mais rápido
  - `0.8` = 20% mais lento

**Nota**: A velocidade é aplicada ao conteúdo principal do short, e as legendas são automaticamente sincronizadas para acompanhar o áudio acelerado.

### 🎬 Configurações de Recorte (Crop Mode)

O sistema permite controlar como o vídeo será recortado para o formato vertical:

- **crop_mode**: Modo de recorte (padrão: "fit")
  - `"fit"` = Mostra todo o conteúdo, redimensiona para caber na largura
  - `"center"` = Recorta ao centro, corta as laterais para manter proporção

**Exemplo de configuração**:
```json
{
    "pattern_video_configuration": {
        "crop_mode": "fit"  // Padrão para todos os vídeos
    },
    "video_configuration": [
        {
            "input_url": "https://www.youtube.com/watch?v=...",
            "crop_mode": "center"  // Configuração específica para este vídeo
        }
    ]
}
```

**Comportamento por formato de vídeo**:
- **Vídeos horizontais** com `"fit"`: Mostra todo o conteúdo lateral
- **Vídeos horizontais** com `"center"`: Recorta ao centro, cortando laterais
- **Vídeos verticais**: Comportamento similar em ambos os modos
- **Vídeos quadrados**: Comportamento similar em ambos os modos

### 🎯 Como Funciona a Sincronização

Quando você configura `content_speed: 1.25`, o sistema:

1. **Calcula duração necessária**: Para 61s finais com 1.25x, precisa de 76.25s originais
2. **Ajusta o corte**: Estende ou reduz o corte para atingir a duração desejada
3. **Acelera o vídeo**: Aplica velocidade 1.25x ao conteúdo
4. **Ajusta legendas**: Recalcula todos os tempos das legendas proporcionalmente
5. **Mantém sincronização**: Áudio e texto permanecem perfeitamente alinhados

**Exemplo**: Para um vídeo final de 61s com velocidade 1.25x:
- Duração original necessária: 61 × 1.25 = 76.25s
- Após aceleração: 76.25s ÷ 1.25 = 61s (objetivo atingido)

### 🎵 Preservação de Pitch

O sistema pode acelerar o vídeo mantendo o pitch original da voz:

- **preserve_pitch: true** (padrão): Mantém o tom da voz original
- **preserve_pitch: false**: Altera o pitch junto com a velocidade (voz fica mais fina/grave)

**Limitações**: A preservação de pitch funciona até 2x de velocidade. Acima disso, o sistema automaticamente usa o método padrão.

### 🎨 Template Dinâmico Inteligente

O sistema agora inclui um template dinâmico que se adapta automaticamente ao formato do vídeo:

#### 🎯 **Adaptação Inteligente de Formato**
- **Vídeos horizontais**: Mostra todo o conteúdo lateral sem cortar
- **Vídeos verticais**: Adapta o molde para aproveitar melhor o espaço
- **Vídeos quadrados**: Ajuste proporcional intermediário

#### 📐 **Layout Dinâmico**
- **Header**: Se posiciona dinamicamente baseado na posição do vídeo
- **Linhas contornantes**: Contornam exatamente as bordas do vídeo
- **Legendas**: Acompanham a borda do vídeo (não mais fixas)
- **Footer**: Centralizado no espaço inferior restante

#### 🎬 **Elementos do Template**
- **Logo "CV"**: Circular com gradiente azul/roxo
- **Texto "CLIPVERSO"**: Título principal em branco
- **Subtitle "CANAL DE CORTES"**: Em azul claro
- **Linhas de separação**: Azul claro, contornam o vídeo
- **Footer**: "Se inscreva • Dé o like • @clipverso-ofc"

#### 🔧 **Posicionamento Inteligente**
- **Header**: 5px acima da borda superior do vídeo
- **Linha superior**: 2px acima da borda superior do vídeo
- **Linha inferior**: 2px abaixo da borda inferior do vídeo
- **Legendas**: Centralizadas horizontalmente, ~55% da altura do quadro
- **Footer**: Centralizado no espaço inferior disponível

### 📝 **Sistema de Legendas Profissional**

O sistema inclui legendas com estilo profissional otimizado para shorts:

#### 🎨 **Estilo Visual**
- **Fonte**: Anton (bold) - fonte local otimizada para legibilidade
- **Cor**: Amarelo #E4EB34 (RGB 228 236 52) - alta visibilidade
- **Contorno**: Preto sólido de 2px - contraste perfeito
- **Texto**: Sempre em MAIÚSCULAS para impacto visual

#### 📐 **Dimensionamento**
- **Tamanho**: ~2.2% da altura do quadro (≈ 42–48px em 1080×1920)
- **Escalabilidade**: Proporcional para outras resoluções
- **Espaçamento**: Line-height 1, sem margens extras

#### 🎯 **Posicionamento**
- **Horizontal**: Centralizado automaticamente
- **Vertical**: ~55% da altura do quadro (ligeiramente abaixo do centro)
- **Responsivo**: Adapta-se a diferentes formatos de vídeo

#### ⚡ **Funcionalidades**
- **Sincronização**: Perfeita com áudio acelerado
- **Segmentação**: Texto dividido em partes menores para melhor legibilidade
- **Destaque**: Palavras-chave destacadas com variações do amarelo
- **Animações**: Fade in/out suaves para transições naturais

### ⏱️ Configuração de Duração

O sistema calcula automaticamente a duração original necessária para atingir a duração final desejada:

- **video_duration**: Duração final do corte em segundos (padrão: 61s)
- **Cálculo automático**: `duração_original = video_duration × content_speed`

**Exemplos**:
- Para 61s finais com 1.25x: precisa de 76.25s originais
- Para 45s finais com 1.5x: precisa de 67.5s originais
- Para 90s finais com 1.0x: precisa de 90s originais

### 🎤 Problema: Voz Fina/Grave

Se você notar que a voz ficou muito fina ou grave após acelerar o vídeo:

1. **Verifique a configuração**: Certifique-se de que `preserve_pitch: true` no `config.json`
2. **Reduza a velocidade**: Use `content_speed: 1.25` em vez de valores maiores
3. **Limite de velocidade**: A preservação de pitch funciona até 2x de velocidade
4. **FFmpeg necessário**: Certifique-se de que o FFmpeg está instalado no sistema

### ⏰ Configurações de Upload

O sistema inclui um delay aleatório entre uploads para evitar detecção de automação:

- **min_seconds**: Tempo mínimo de espera (padrão: 1800s = 30 minutos)
- **max_seconds**: Tempo máximo de espera (padrão: 3600s = 1 hora)

Para desabilitar o delay, configure ambos como `0`:
```json
"upload_delay": {
    "min_seconds": 0,
    "max_seconds": 0
}
```

## Uso

O sistema funciona em duas etapas separadas para maior robustez:

### 1. 🎬 Geração de Cortes
```bash
poetry run python main.py
```

O sistema irá:
- Processar todos os vídeos configurados no `config.json`
- Baixar os vídeos
- Transcrever o áudio
- Selecionar os melhores momentos
- Criar os cortes com legendas
- Anexar outros (se configurado)
- Salvar checkpoint para upload posterior

### 2. 📤 Upload para YouTube
```bash
poetry run python upload_clips.py
```

O sistema irá:
- Carregar checkpoint de upload
- Fazer upload de cada corte
- Respeitar delays configurados
- Gerar relatório de sucesso/falhas

### 🔍 Verificar Status
```bash
python check_status.py
```

Mostra o status atual do sistema e próximos passos.

## Sistema de Checkpoints

O sistema implementa checkpoints robustos para garantir que nenhum progresso seja perdido:

### 🔄 Checkpoint de Processamento
- Salvo durante a geração de cada corte
- Permite retomar processamento interrompido
- Valida URL do episódio para evitar conflitos

### 📤 Checkpoint de Upload
- Salvo após geração de todos os cortes
- Contém informações de todos os cortes prontos
- Permite upload posterior com delays configurados

### 🛡️ Recuperação de Falhas
- **Queda de energia**: Retoma do último checkpoint
- **Erro de upload**: Mantém checkpoint para retry
- **Processamento interrompido**: Continua de onde parou

## Estrutura de Diretórios

```
podcast-cuts/
├── assets/        # Assets do projeto
│   └── outros/    # Outros gerados (outro1.mp4, outro2.mp4, outro3.mp4)
├── clips/          # Cortes gerados
│   └── Nome_do_Video/  # Diretório específico por vídeo
│       ├── corte1.mp4
│       ├── corte1_com_outro.mp4  # Corte com outro anexado
│       ├── corte1_metadata.txt
│       ├── corte2.mp4
│       └── corte2_metadata.txt
├── raw/           # Vídeos originais
├── logs/          # Logs de erros e custos
├── modules/       # Módulos do sistema
├── fonts/         # Fontes para legendas
├── config.json    # Configurações
├── .env           # Variáveis de ambiente
├── molde.png      # Molde para outros
├── logo.png       # Logo do ClipVerso
├── main.py        # Script principal
├── generate_outros.py  # Gerador de outros
├── list_clips.py  # Lista vídeos processados
└── upload_clips.py # Upload para YouTube
```

## Sistema de Outros

O ClipVerso inclui um sistema automatizado de outros que adiciona um call-to-action padronizado ao final de cada corte.

### 🎬 Características dos Outros

- **3 Variações**: Sistema gera 3 outros diferentes para evitar repetição
- **TTS em Português**: Voz sintética pedindo like, inscrição e comentários
- **Animações**: Textos animados com efeitos de escala e fade
- **Branding**: Logo "CV" e identidade visual do ClipVerso
- **Duração**: 5 segundos, formato vertical 1080x1920

### 🔧 Como Usar

1. **Gerar Outros** (primeira vez):
   ```bash
   python generate_outros.py
   ```

2. **Configurar** (opcional):
   ```json
   // config.json
   "append_outro": true  // true = anexa outro automaticamente
   ```

### 📁 Arquivos Gerados

- `assets/outros/outro1.mp4` - Primeira variação
- `assets/outros/outro2.mp4` - Segunda variação  
- `assets/outros/outro3.mp4` - Terceira variação

### 🎯 Integração Automática

O sistema automaticamente:
- Escolhe um outro aleatório para cada corte
- Anexa o outro ao final do vídeo
- Mantém o corte original como backup
- Gera arquivo `corte_com_outro.mp4` para upload

## Scripts Utilitários

### Verificar Status do Sistema
Para verificar o status atual e próximos passos:
```bash
python check_status.py
```

### Listar Vídeos Processados
Para ver todos os vídeos processados e seus cortes:
```bash
python list_clips.py
```

### Gerenciar Token do YouTube
Para gerenciar autenticação do YouTube:
```bash
python manage_token.py status    # Verifica status do token
python manage_token.py test      # Testa autenticação
python manage_token.py clear     # Remove token cache
python manage_token.py auth      # Força nova autenticação
```

### Limpar Arquivos Temporários
Para limpar arquivos temporários que podem causar problemas:
```bash
python cleanup_temp_files.py
```

### Gerar Outros do ClipVerso
Para gerar os outros padronizados do canal:
```bash
python generate_outros.py
```

Este script cria 3 variações de outros com:
- TTS em português brasileiro
- Animações baseadas no molde do ClipVerso
- Textos engajantes ("Curtiu? Deixa o like 👍", etc.)
- Duração de 5 segundos, formato 1080x1920

**Atualizar Outros:**
Para atualizar os outros com versões melhoradas:
```bash
python update_outros.py
```

Este script faz backup dos outros antigos e gera novos com animações aprimoradas.

**Gerador de Outros Melhorado:**
O arquivo `generate_outros_enhanced.py` contém uma versão avançada do gerador com:
- Animações mais fluidas e criativas
- Efeitos visuais aprimorados
- Sincronização perfeita com TTS
- Partículas e elementos flutuantes
- Logo animado com efeitos

### Exemplo de API REST
O arquivo `api_example.py` demonstra como seria uma futura API REST para o sistema, incluindo:
- Endpoints para processamento de vídeos
- Sistema de jobs assíncronos
- Validação de payload
- Monitoramento de status

## Otimizações de Performance

O sistema inclui várias otimizações para acelerar o processamento:

### 🚀 Aceleração por GPU AMD
- Detecta automaticamente GPUs AMD
- Usa codec `h264_amf` para aceleração por hardware
- Configurável via `config.json`

### ⚡ Otimizações de CPU
- Presets otimizados do FFmpeg
- Processamento paralelo
- Configurações de qualidade ajustáveis

### 🎯 Configurações de Qualidade
- **fast**: Máxima velocidade, qualidade reduzida
- **balanced**: Equilíbrio entre velocidade e qualidade
- **high**: Melhor qualidade, velocidade reduzida

### 📊 Configuração no config.json
```json
"video_optimization": {
    "use_gpu": true,          // Usa GPU AMD se disponível
    "quality": "balanced",     // fast, balanced, high
    "enable_parallel": true    // Processamento paralelo
}
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

**Gerenciamento de Dependências:**
- `pyproject.toml`: Configuração do Poetry e dependências
- `poetry.lock`: Versões exatas das dependências (não edite manualmente)
- `requirements.txt`: Dependências para instalação sem Poetry

## Solução de Problemas

1. **Erro no ImageMagick**:
   - Verifique se o caminho no `moviepy_config.py` está correto
   - Execute `python install_imagemagick.py` novamente

2. **Erro na API do YouTube**:
   - Verifique se o `client_secret.json` está presente
   - Confirme se as credenciais têm permissão para upload
   - Use `python manage_token.py auth` para reautenticar

3. **Erro na API OpenAI**:
   - Verifique se a chave API está correta no `.env`
   - Confirme se tem créditos suficientes

4. **Erro no codec AMD (h264_amf)**:
   - Se o codec falhar, o sistema automaticamente usa fallback para CPU
   - Para desabilitar GPU AMD, configure `use_gpu: false` no `config.json`
   - Verifique se o FFmpeg tem suporte AMD instalado

5. **Processamento muito lento**:
   - Configure `quality: fast` no `config.json`
   - Reduza `highlights` para 1
   - Use `whisper_size: tiny`
   - Feche outros programas durante o processamento

6. **Arquivos temporários causando problemas**:
   - Execute `python cleanup_temp_files.py` para limpar
   - Reinicie o sistema se necessário

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Arquivos Ignorados pelo Git

O arquivo `.gitignore` configura quais arquivos não são versionados:

- **Credenciais**: `.env`, `client_secret.json`, `token.json`
- **Ambiente virtual**: `venv/`
- **Cache Python**: `__pycache__/`, `*.pyc`
- **Mídia**: `raw/`, `clips/`
- **Logs**: `logs/`, `*.log`
- **Sistema**: `.DS_Store`, `Thumbs.db`

**Importante**: Nunca commite arquivos com credenciais reais. Use sempre os arquivos de exemplo.

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 