<div align="center">

# 🔎 ChassiScan

**Leitura automatizada de números de chassi (VIN) a partir de imagens, com validação conforme a norma ISO 3779.**

![CI](https://github.com/EdsonOliveira18/chassiscan/actions/workflows/ci.yml/badge.svg?branch=main)
![CD](https://github.com/EdsonOliveira18/chassiscan/actions/workflows/cd.yml/badge.svg?branch=main)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![EasyOCR](https://img.shields.io/badge/EasyOCR-PyTorch-EE4C2C?logo=pytorch&logoColor=white)](https://github.com/JaidedAI/EasyOCR)
[![Docker](https://img.shields.io/badge/Docker-2496ED?logo=docker&logoColor=white)](https://www.docker.com)
[![GHCR](https://img.shields.io/badge/registry-GHCR-181717?logo=github&logoColor=white)](https://github.com/EdsonOliveira18/chassiscan/pkgs/container/chassiscan)
[![Terraform](https://img.shields.io/badge/Terraform-7B42BC?logo=terraform&logoColor=white)](https://www.terraform.io)
[![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000)](https://github.com/psf/black)
[![Release](https://img.shields.io/badge/release-v2.0.0--fase2-blue)](https://github.com/EdsonOliveira18/chassiscan/releases)

</div>

---

## 📌 Sobre o projeto

A conferência manual do número de chassi em pátios, vistorias e seguradoras é
lenta, repetitiva e sujeita a erro humano — um único caractere trocado invalida
o registro. O **ChassiScan** automatiza esse processo: recebe uma imagem,
extrai o **VIN** via OCR, valida o código e devolve o resultado por
**API REST** ou **CLI**.

> ### 🎯 Fase 2 — Entrega Contínua (CD)
> Esta entrega evolui a base da Fase 1 com um **pipeline de entrega contínua**:
> a cada merge na `main`, a imagem Docker é construída, versionada e publicada
> automaticamente no **GitHub Container Registry (GHCR)**, com cache de layers,
> autenticação sem segredos fixos e acionamento manual via `workflow_dispatch`.

<details>
<summary><b>✅ Fase 1 — Configuração e Automação Inicial (concluída)</b></summary>

Versionamento disciplinado com branch protegida, containerização multi-stage,
infraestrutura como código em Terraform, suíte de testes segmentada por
marcadores e pipeline de integração contínua com gate de qualidade.

</details>

---

## 🧱 Stack

| Camada | Tecnologia |
| :--- | :--- |
| Linguagem | Python 3.12 |
| API | FastAPI + Uvicorn |
| OCR | EasyOCR (PyTorch CPU) |
| Processamento de imagem | OpenCV / Pillow / scikit-image |
| Testes | Pytest + pytest-cov |
| Qualidade de código | Ruff + Black |
| Container | Docker (multi-stage) + Docker Compose |
| Registry | GitHub Container Registry (GHCR) |
| Infraestrutura | Terraform (AWS) |
| CI/CD | GitHub Actions |

---

## 📂 Estrutura do projeto

```text
chassiscan/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                  # integração contínua
│   │   └── cd.yml                  # entrega contínua (build + push GHCR)
│   └── pull_request_template.md    # checklist padrão de PR
├── app/
│   ├── __init__.py
│   ├── api.py                      # rotas FastAPI
│   ├── cli.py                      # interface de linha de comando
│   ├── config.py                   # configuração via variáveis de ambiente
│   ├── image_utils.py              # pré-processamento da imagem
│   ├── ocr_engine.py               # integração com o EasyOCR
│   └── vin_utils.py                # normalização e validação do VIN
├── tests/
│   ├── conftest.py                 # fixtures compartilhadas
│   ├── test_unit_vin.py            # marcador: unit
│   ├── test_integration_api.py     # marcador: integration
│   └── test_accuracy.py            # marcador: accuracy
├── infra/
│   ├── backend.tf                  # state remoto (S3) + lock (DynamoDB)
│   ├── providers.tf                # provider AWS + default_tags
│   ├── main.tf                     # recursos da infraestrutura
│   ├── variables.tf                # variáveis tipadas
│   ├── outputs.tf                  # saídas do módulo
│   └── envs/
│       ├── dev.tfvars
│       └── prod.tfvars
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── pyproject.toml
├── .gitignore
└── README.md
```

---

## 🔄 Arquitetura

```mermaid
flowchart TD
    A[Imagem<br/>upload ou caminho local] --> B[image_utils.py<br/>grayscale · threshold<br/>deskew · denoise]
    B --> C[ocr_engine.py<br/>EasyOCR / PyTorch CPU<br/>allowlist A-Z 0-9]
    C --> D[vin_utils.py<br/>17 caracteres · sem I O Q<br/>dígito verificador ISO 3779]
    D --> E[api.py<br/>FastAPI]
    D --> F[cli.py<br/>linha de comando]
    E --> G[JSON<br/>vin · valido · confianca]
    F --> G
```

---

## ⚙️ Pré-requisitos

- Python **3.12+**
- Docker e Docker Compose *(opcional, recomendado)*
- Terraform **1.9+** *(apenas para a infraestrutura)*

> [!NOTE]
> Não há dependência de OCR externa. O **EasyOCR** baixa os modelos de
> reconhecimento automaticamente no primeiro uso e os mantém em cache
> (`EASYOCR_MODULE_PATH`), o que torna a primeira execução mais lenta.

---

## 🚀 Execução local

```bash
# 1. clonar o repositório
git clone https://github.com/EdsonOliveira18/chassiscan.git
cd chassiscan

# 2. criar e ativar o ambiente virtual
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# 3. instalar as dependências
pip install -r requirements.txt

# 4. subir a API
uvicorn app.api:app --reload --port 8000
```

📖 Documentação interativa: **http://localhost:8000/docs**

> [!TIP]
> No **PowerShell**, `curl` é apelido de `Invoke-WebRequest`. Para testar,
> use `Invoke-RestMethod http://localhost:8000/health` ou chame o binário
> real com `curl.exe`.

---

## 🐳 Execução com Docker

```bash
docker compose up -d --build   # sobe o ambiente em http://localhost:8000
docker compose ps              # o serviço deve ficar "healthy"
docker compose logs -f api     # acompanha os logs
docker compose down            # encerra e remove os contêineres
```

A imagem usa build **multi-stage** (sem toolchain de compilação no runtime),
executa com **usuário não-root** e expõe um **healthcheck** em `/health`.

### 📦 Consumindo a imagem publicada no GHCR

```bash
docker pull ghcr.io/edsonoliveira18/chassiscan:latest
docker run --rm -p 8000:8000 ghcr.io/edsonoliveira18/chassiscan:latest
```

Tags disponíveis: `latest` (última `main`) e `sha-<commit>` (imutável, ideal
para rollback).

---

## 🌐 Endpoints da API

| Método | Rota | Descrição |
| :--- | :--- | :--- |
| `GET` | `/health` | Verificação de disponibilidade do serviço |
| `POST` | `/vin/extract` | Recebe uma imagem e retorna o VIN identificado |
| `GET` | `/docs` | Documentação OpenAPI (Swagger UI) |

**Requisição**

```bash
curl -X POST http://localhost:8000/vin/extract \
  -F "file=@exemplos/chassi.jpg"
```

**Resposta**

```json
{
  "vin": "1HGCM82633A004352",
  "valido": true,
  "confianca": 0.94
}
```

| Código | Significado |
| :--- | :--- |
| `200` | VIN extraído com sucesso |
| `422` | Arquivo inválido ou imagem ilegível |
| `500` | Erro interno no processamento |

---

## 💻 Uso via CLI

```bash
python -m app.cli --imagem exemplos/chassi.jpg
python -m app.cli --imagem exemplos/chassi.jpg --json
```

---

## 🧪 Testes e qualidade

```bash
# análise estática e formatação
ruff check app tests
black --check app tests

# suíte completa com cobertura
pytest

# execução por categoria
pytest -m unit
pytest -m integration
pytest -m accuracy
```

Configuração centralizada no `pyproject.toml`:

```toml
[tool.pytest.ini_options]
addopts = "-q --cov=app --cov-report=term-missing --cov-report=xml"
testpaths = ["tests"]
markers = [
  "unit: testes unitarios rapidos",
  "integration: testes de integracao da API",
  "accuracy: gate de acuracia do OCR",
]
```

O arquivo `coverage.xml` é gerado a cada execução e publicado como **artefato
do pipeline**.

---

## ☁️ Infraestrutura (Terraform)

O estado é mantido em **backend remoto S3** com **lock em DynamoDB**, e os
ambientes são separados por arquivos `.tfvars` reutilizando o mesmo código.

```bash
cd infra

terraform init
terraform fmt -check
terraform validate

# desenvolvimento
terraform plan  -var-file=envs/dev.tfvars
terraform apply -var-file=envs/dev.tfvars

# produção
terraform plan  -var-file=envs/prod.tfvars
terraform apply -var-file=envs/prod.tfvars
```

Validação sem credenciais da nuvem (a mesma usada no CI):

```bash
terraform init -backend=false && terraform validate
```

> [!WARNING]
> Arquivos de estado (`*.tfstate`) e o diretório `.terraform/` são ignorados
> pelo Git e **nunca** devem ser versionados.

---

## 🔁 Pipeline de CI

Definido em `.github/workflows/ci.yml`, disparado em `push` e `pull_request`
para a branch `main`.

| Ordem | Job | Ferramentas | Falha quando |
| :---: | :--- | :--- | :--- |
| 1 | `lint` | Ruff, Black | há violação de estilo |
| 2 | `test` | Pytest + coverage | teste falha ou cobertura fica abaixo do mínimo |
| 3 | `docker` | Docker Buildx | o build da imagem falha |
| 4 | `terraform` | `fmt -check`, `validate` | código não formatado ou inválido |

> [!IMPORTANT]
> A branch `main` é **protegida**: exige Pull Request e **status check do CI
> verde**, com push direto bloqueado.

---

## 🚢 Pipeline de CD

Definido em `.github/workflows/cd.yml`, disparado em `push` na `main` e
manualmente via `workflow_dispatch`.

| Ordem | Etapa | Descrição |
| :---: | :--- | :--- |
| 1 | Checkout + Buildx | prepara o builder com cache `type=gha` |
| 2 | Login no GHCR | autenticação via `GITHUB_TOKEN` (sem segredo fixo) |
| 3 | Build & Push | publica as tags `latest` e `sha-<commit>` |
| 4 | Resumo | registra as tags publicadas no *summary* do run |

Permissões mínimas exigidas no workflow:

```yaml
permissions:
  contents: read
  packages: write
```

Aceleração do build com cache de layers do Actions:

```yaml
- uses: docker/build-push-action@v6
  with:
    context: .
    push: true
    tags: |
      ghcr.io/${{ github.repository }}:latest
      ghcr.io/${{ github.repository }}:sha-${{ github.sha }}
    cache-from: type=gha
    cache-to: type=gha,mode=max
```

> [!NOTE]
> O primeiro build é mais demorado (~8–12 min) por causa do download do
> PyTorch CPU e do scikit-image. Com o cache ativo, as execuções seguintes
> caem para poucos minutos.

---

## 🤝 Fluxo de contribuição

**1. Crie uma branch a partir da `main`**

```bash
git checkout -b feat/nome-da-funcionalidade
```

Prefixos aceitos: `feat/` · `fix/` · `chore/` · `docs/` · `test/`

**2. Faça commits no padrão Conventional Commits**

```text
feat(ocr): adiciona deskew automatico na imagem
fix(vin): corrige calculo do digito verificador
chore(infra): cria backend remoto S3 + DynamoDB lock
ci(cd): publica imagem no GHCR com cache de layers
test(api): cobre retorno 422 para arquivo invalido
docs(readme): documenta execucao via docker compose
```

**3. Valide localmente antes de abrir o PR**

```bash
ruff check app tests && black --check app tests && pytest
```

**4. Abra o Pull Request**, preencha o template e aguarde o CI ficar verde.

---

## 🔧 Variáveis de ambiente

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `CHASSISCAN_MIN_CONF` | `0.45` | Confiança mínima aceita na extração |
| `CHASSISCAN_MAX_VARIANTS` | `6` | Máximo de variantes testadas na normalização |
| `EASYOCR_MODULE_PATH` | `/app/.easyocr` | Diretório de cache dos modelos de OCR |
| `LOG_LEVEL` | `INFO` | Nível de log da aplicação |
| `API_PORT` | `8000` | Porta de exposição da API |

> [!NOTE]
> Para uso local, crie um arquivo `.env` a partir do modelo. Ele está no
> `.gitignore` e não deve ser versionado.

---

## 🗺️ Roadmap

- [x] **Fase 1** — versionamento, container, IaC, testes e CI
- [x] **Fase 2** — entrega contínua (CD) com publicação da imagem no GHCR
- [x] **Fase 2** — versionamento de imagem por `sha` e cache de layers
- [ ] **Fase 3** — observabilidade: logs estruturados e métricas
- [ ] **Fase 3** — varredura de vulnerabilidades (Trivy) e autenticação OIDC na AWS
- [ ] **Fase 3** — ampliação do dataset e elevação do gate de acurácia

---

## 📄 Licença

Projeto acadêmico desenvolvido para a disciplina de **DevOps & Integração
Contínua** do curso de **Análise e Desenvolvimento de Sistemas**.

<div align="center">
<sub>Desenvolvido por <b>Edson</b> · Fase 2 · v2.0.0-fase2</sub>
</div>
