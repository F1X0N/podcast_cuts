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

# Configurações de otimização de vídeo
video_optimization:
  use_gpu: true          # true = usa GPU AMD se disponível
  quality: balanced       # fast, balanced, high
  enable_parallel: true   # true = processamento paralelo quando possível

# Configurações de outros
append_outro: true        # true = anexa outro ao final de cada corte
content_speed: 1.25       # velocidade do conteúdo principal (1.0 = normal, 1.25 = 25% mais rápido)

# Configurações de upload
upload_delay:
  min_seconds: 3600       # Delay mínimo entre uploads (1 hora)
  max_seconds: 5400       # Delay máximo entre uploads (1.5 horas)
```

### ⚡ Configurações de Velocidade

O sistema permite controlar a velocidade do conteúdo principal dos shorts:

- **content_speed**: Velocidade do conteúdo (padrão: 1.25x = 25% mais rápido)
  - `1.0` = velocidade normal
  - `1.25` = 25% mais rápido (padrão recomendado)
  - `1.5` = 50% mais rápido
  - `0.8` = 20% mais lento

**Nota**: A velocidade é aplicada ao conteúdo principal do short, e as legendas são automaticamente sincronizadas para acompanhar o áudio acelerado.

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

1. **Verifique a configuração**: Certifique-se de que `preserve_pitch: true` no `config.yaml`
2. **Reduza a velocidade**: Use `content_speed: 1.25` em vez de valores maiores
3. **Limite de velocidade**: A preservação de pitch funciona até 2x de velocidade
4. **FFmpeg necessário**: Certifique-se de que o FFmpeg está instalado no sistema

### ⏰ Configurações de Upload

O sistema inclui um delay aleatório entre uploads para evitar detecção de automação:

- **min_seconds**: Tempo mínimo de espera (padrão: 3600s = 1 hora)
- **max_seconds**: Tempo máximo de espera (padrão: 5400s = 1.5 horas)

Para desabilitar o delay, configure ambos como `0`:
```yaml
upload_delay:
  min_seconds: 0
  max_seconds: 0
```

## Uso

O sistema agora funciona em duas etapas separadas para maior robustez:

### 1. 🎬 Geração de Cortes
```bash
poetry run python main.py "URL_DO_PODCAST"
```

O sistema irá:
- Baixar o vídeo
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

### ⚡ Testar Configuração de Velocidade
```bash
python test_speed.py
```

Mostra a configuração atual de velocidade e como alterá-la.

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
│       ├── corte1_metadata.json
│       ├── corte2.mp4
│       └── corte2_metadata.json
├── raw/           # Vídeos originais
├── logs/          # Logs de erros e custos
├── modules/       # Módulos do sistema
├── fonts/         # Fontes para legendas
├── config.yaml    # Configurações
├── .env           # Variáveis de ambiente
├── main.py        # Script principal
├── generate_outros.py  # Gerador de outros
├── test_outros.py      # Teste do sistema de outros
├── list_clips.py  # Lista vídeos processados
└── copy_metadata.py # Copia metadados para área de transferência
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

2. **Testar Sistema**:
   ```bash
   python test_outros.py
   ```

3. **Configurar** (opcional):
   ```yaml
   # config.yaml
   append_outro: true  # true = anexa outro automaticamente
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

## Sistema de Checkpoint

O sistema implementa um mecanismo robusto de checkpoint para permitir a retomada de processamento interrompido e evitar conflitos em execuções paralelas.

### 🔄 Funcionalidades do Checkpoint

- **Retomada de Processamento**: Se o script for interrompido, pode continuar de onde parou
- **Validação de URL**: Verifica se o checkpoint pertence ao episódio correto
- **Segurança em Paralelo**: Evita que execuções paralelas usem checkpoints de outros episódios
- **Validação de Arquivos**: Confirma se os arquivos de vídeo ainda existem

### 🛡️ Validações Implementadas

1. **Existência do Arquivo**: Verifica se o arquivo `checkpoint.json` existe
2. **URL do Episódio**: Compara a URL do checkpoint com a URL atual
3. **Arquivo de Vídeo**: Confirma se o arquivo de vídeo referenciado ainda existe
4. **Integridade JSON**: Valida se o arquivo JSON está correto

### 📝 Estrutura do Checkpoint

```json
{
  "video_path": "raw/VIDEO_ID.mp4",
  "highlight": {
    "idx": 1,
    "hook": "Título do corte",
    "tags": ["tag1", "tag2"]
  },
  "transcript": [...],
  "video_info": {...},
  "episode_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "created_at": "2024-01-01 12:00:00"
}
```

### ⚠️ Comportamento em Execuções Paralelas

- Se duas instâncias do script rodarem simultaneamente com URLs diferentes, cada uma terá seu próprio checkpoint
- O sistema automaticamente detecta e rejeita checkpoints de outros episódios
- Mensagens claras indicam quando um checkpoint é rejeitado e por quê

## Scripts Utilitários

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

### Testar Sistema de Outros
Para validar se os outros estão funcionando:
```bash
python test_outros.py
```

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

### Copiar Metadados
Para copiar os metadados de um corte específico para a área de transferência:
```bash
python copy_metadata.py "Nome_do_Video" "Titulo_do_Corte"
```

**Exemplo:**
```bash
python copy_metadata.py "Podcast_Flow_123" "Momentos_Incriveis"
```

Isso copiará título, descrição, tags e informações do vídeo original para facilitar o uso em outras redes sociais.

### Testar Validação de Checkpoint
Para testar o sistema de validação de checkpoint:
```bash
python test_checkpoint_validation.py
```

Este script demonstra como o sistema valida checkpoints para evitar conflitos em execuções paralelas.

### Testar Otimizações
Para testar e configurar as otimizações de vídeo:
```bash
python test_optimization.py
```

Para executar benchmark completo:
```bash
python test_optimization.py --benchmark
```

### Testar Codec AMD
Para testar especificamente o codec AMD:
```bash
python test_amd_codec.py
```

## Otimizações de Performance

O sistema inclui várias otimizações para acelerar o processamento:

### 🚀 Aceleração por GPU AMD
- Detecta automaticamente GPUs AMD
- Usa codec `h264_amf` para aceleração por hardware
- Configurável via `config.yaml`

### ⚡ Otimizações de CPU
- Presets otimizados do FFmpeg
- Processamento paralelo
- Configurações de qualidade ajustáveis

### 🎯 Configurações de Qualidade
- **fast**: Máxima velocidade, qualidade reduzida
- **balanced**: Equilíbrio entre velocidade e qualidade
- **high**: Melhor qualidade, velocidade reduzida

### 📊 Configuração no config.yaml
```yaml
video_optimization:
  use_gpu: true          # Usa GPU AMD se disponível
  quality: balanced       # fast, balanced, high
  enable_parallel: true   # Processamento paralelo
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

4. **Erro no codec AMD (h264_amf):**
   - Execute `python test_amd_codec.py` para diagnosticar
   - Se o codec falhar, o sistema automaticamente usa fallback para CPU
   - Para desabilitar GPU AMD, configure `use_gpu: false` no `config.yaml`
   - Verifique se o FFmpeg tem suporte AMD instalado

5. **Processamento muito lento:**
   - Configure `quality: fast` no `config.yaml`
   - Reduza `highlights` para 1
   - Use `whisper_size: tiny`
   - Feche outros programas durante o processamento

## Contribuindo

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes. 