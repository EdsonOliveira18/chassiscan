# ChassiScan API — Fase 1: Configuração e Automação Inicial

![CI](https://github.com/EdsonOliveira18/chassiscan/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.11%2B-blue)
![Terraform](https://img.shields.io/badge/Terraform-1.9-844FBA)
![License](https://img.shields.io/badge/license-MIT-green)

## 🔗 Links de acesso

| Recurso | Link |
|---|---|
| **Repositório (código-fonte)** | https://github.com/EdsonOliveira18/chassiscan|
| **Pipeline de CI (execuções)** | https://github.com/EdsonOliveira18/chassiscan/actions |
| **Workflow de CI** | [`.github/workflows/ci.yml`](.github/workflows/ci.yml) |
| **Scripts de IaC (Terraform)** | [`infra/`](infra/) |
| **Testes automatizados** | [`tests/`](tests/) |

> **Aluno:** Edson Oliveira· **Curso:** Análise e Desenvolvimento de Sistemas · **Disciplina:** DevOps · **Fase:** 1 · **Semestre:** 2026/3

## 1.1 Descrição do projeto

O **ChassiScan** é uma API REST em **FastAPI** que realiza a leitura automática do número de chassi veicular (**VIN — Vehicle Identification Number**) a partir de imagens, usando pré-processamento digital (OpenCV) e OCR (Tesseract).

**Problema:** em pátios, vistorias e oficinas, os 17 caracteres do chassi são lidos e digitados manualmente — processo lento e sujeito a erro, sobretudo pela confusão entre `0`/`O`, `1`/`I` e `5`/`S`.

**Solução:** o operador envia uma foto e a API retorna o VIN normalizado, validado pelo dígito verificador oficial (ISO 3779), com índice de confiança.

**Recorte da Fase 1:** o foco desta entrega é **DevOps** — esteira de integração contínua, automação de build/testes e provisionamento de infraestrutura como código. A aplicação é o objeto sobre o qual a automação é exercida.

## 1.2 Objetivos

### Objetivo geral
Estabelecer a base de automação (CI + IaC) que garanta build, testes e provisionamento reprodutíveis para a ChassiScan API.

### Objetivos específicos
1. Versionar o projeto em repositório Git público no GitHub, com fluxo de branches definido.
2. Implementar pipeline de CI no **GitHub Actions** executando lint, testes e cobertura a cada push/PR.
3. Implementar testes automatizados integrados ao pipeline, com gate mínimo de cobertura.
4. Descrever a infraestrutura necessária e provisioná-la via **Terraform** (IaC).
5. Empacotar a aplicação em imagem **Docker**, garantindo paridade entre ambientes.
6. Documentar o processo para que qualquer pessoa reproduza o ambiente do zero.

## 1.3 Requisitos

### Requisitos funcionais da aplicação

| ID | Requisito | Status |
|---|---|---|
| RF01 | Receber imagem via HTTP (`multipart/form-data`) | ✅ |
| RF02 | Extrair texto da imagem via OCR | ✅ |
| RF03 | Normalizar caracteres ambíguos (`O→0`, `I→1`, `Q→0`, `S→5`) | ✅ |
| RF04 | Validar o dígito verificador do VIN (ISO 3779) | ✅ |
| RF05 | Retornar resultado em JSON com índice de confiança | ✅ |
| RF06 | Rejeitar arquivo vazio (HTTP 400) | ✅ |
| RF07 | Rejeitar arquivo acima de 10 MB (HTTP 413) | ✅ |
| RF08 | Expor endpoint de *health check* (`/health`) | ✅ |
| RF09 | Documentar a API automaticamente (OpenAPI/Swagger) | ✅ |

### Requisitos de DevOps (escopo desta fase)

| ID | Requisito | Status |
|---|---|---|
| RD01 | Repositório Git no GitHub com README e `.gitignore` | ✅ |
| RD02 | Pipeline de CI disparado em `push` e `pull_request` | ✅ |
| RD03 | Etapa de lint automatizada (Ruff) | ✅ |
| RD04 | Etapa de testes automatizados (Pytest) integrada ao CI | ✅ |
| RD05 | Relatório de cobertura publicado como artefato | ✅ |
| RD06 | Build da imagem Docker validado no pipeline | ✅ |
| RD07 | Infraestrutura descrita em código (Terraform) | ✅ |
| RD08 | Validação automática do IaC (`fmt -check`, `validate`) no CI | ✅ |
| RD09 | Segredos gerenciados via GitHub Secrets (nunca no código) | ✅ |
| RD10 | Proteção da branch `main` exigindo CI verde | ✅ |

### Requisitos não funcionais

| ID | Requisito | Critério de aceite |
|---|---|---|
| RNF01 | Desempenho | Resposta ≤ 3 s por imagem |
| RNF02 | Limite de upload | 10 MB |
| RNF03 | Cobertura de testes | ≥ 80% (pipeline falha abaixo disso) |
| RNF04 | Padrão de código | PEP 8, validado por Ruff |
| RNF05 | Duração do pipeline | ≤ 5 min |
| RNF06 | Portabilidade | Windows, Linux e macOS; execução via Docker |
| RNF07 | Reprodutibilidade | Versões fixadas em `requirements.txt` e `.terraform.lock.hcl` |
| RNF08 | Observabilidade | Logs estruturados + `/health` para *health check* |

## 1.4 Plano de Integração Contínua

### Estratégia de branches (GitHub Flow)

| Branch | Finalidade | Proteção |
|---|---|---|
| `main` | Código estável e entregável | PR obrigatório + CI verde |
| `feature/*` | Desenvolvimento de funcionalidades | — |
| `fix/*` | Correções | — |

**Padrão de commits:** Conventional Commits (`feat:`, `fix:`, `test:`, `ci:`, `docs:`, `refactor:`).

### Gatilhos do pipeline

| Evento | Ação |
|---|---|
| `push` em `main` | Pipeline completo |
| `push` em `feature/*` e `fix/*` | Pipeline completo |
| `pull_request` → `main` | Pipeline completo (bloqueia merge se falhar) |
| `workflow_dispatch` | Execução manual |

### Estágios do pipeline

| # | Estágio | Ferramenta | Critério de falha |
|---|---|---|---|
| 1 | Checkout | `actions/checkout` | — |
| 2 | Setup do ambiente | `actions/setup-python` (3.11 e 3.12) | — |
| 3 | Cache de dependências | `actions/cache` (pip) | — |
| 4 | Dependências de sistema | `apt-get install tesseract-ocr` | Falha na instalação |
| 5 | Instalação de pacotes | `pip install -r requirements.txt` | Conflito de versões |
| 6 | Lint / formatação | `ruff check` + `ruff format --check` | Qualquer violação |
| 7 | Testes + cobertura | `pytest --cov=app --cov-fail-under=80` | Teste falho ou cobertura < 80% |
| 8 | Artefatos | `actions/upload-artifact` (HTML de cobertura) | — |
| 9 | Build Docker | `docker build` | Falha no build |
| 10 | Validação do IaC | `terraform fmt -check` + `validate` | Sintaxe/formatação inválida |

### Matriz de execução
Sistema operacional `ubuntu-latest`, Python **3.11** e **3.12** em paralelo — garante compatibilidade em ambas as versões.

### Política de qualidade (*quality gates*)
- Nenhum merge em `main` sem pipeline verde.
- Cobertura mínima de 80% imposta pelo próprio comando de teste.
- Zero avisos de lint tolerados.

### Gestão de segredos
Credenciais (ex.: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`) ficam em **GitHub Secrets**, injetadas como variáveis de ambiente. Não há credencial no repositório; `.env` está no `.gitignore`.

### Plano de Entrega Contínua (preparação para a próxima fase)
Imagem Docker versionada por *tag* → publicação em registry → *deploy* automático em ambiente de *staging* → promoção manual para produção, com *rollback* pela imagem anterior.

## 1.5 Especificação da infraestrutura necessária

### Visão geral

```
Internet
   │  HTTP :80/:8000
   ▼
Security Group (80, 8000, 22 restrito)
   │
   ▼
EC2 t3.micro (Amazon Linux 2023)
   ├── Docker Engine
   └── Container: chassiscan-api (FastAPI + Tesseract)
        │
        ▼
   S3 Bucket — armazenamento de imagens e artefatos
```

### Recursos provisionados

| Recurso | Especificação | Justificativa |
|---|---|---|
| VPC + Subnet pública | CIDR `10.0.0.0/16` / `10.0.1.0/24` | Isolamento de rede |
| Internet Gateway + Route Table | Rota `0.0.0.0/0` | Acesso público à API |
| Security Group | Entrada: 80, 8000 (público) e 22 (IP restrito); saída: liberada | Superfície de exposição mínima |
| EC2 | `t3.micro`, Amazon Linux 2023, 20 GB gp3 | Suficiente para OCR de baixo volume; elegível ao *free tier* |
| S3 Bucket | Versionamento e criptografia AES-256 ativados | Guarda imagens processadas e artefatos |
| IAM Role + Instance Profile | Permissão restrita ao bucket do projeto | Princípio do menor privilégio |
| Key Pair | Chave SSH para administração | Acesso operacional |

### Requisitos de software na instância

| Item | Versão |
|---|---|
| Docker Engine | 24+ |
| Python (imagem base) | 3.11-slim |
| Tesseract OCR | 5.0+ |

### Dimensionamento e custos

| Item | Estimativa mensal |
|---|---|
| EC2 `t3.micro` | US$ ~7,50 (ou US$ 0 no *free tier*) |
| S3 (5 GB) | US$ ~0,12 |
| Transferência de dados | US$ ~1,00 |
| **Total aproximado** | **US$ ~8,60** |

### Ferramenta de IaC escolhida
**Terraform** — sintaxe declarativa (HCL), *state* explícito, `plan` antes do `apply` e portabilidade entre provedores. Vantagem sobre o CloudFormation neste contexto: menor verbosidade e independência de fornecedor.

### Ambientes

| Ambiente | Finalidade | Workspace Terraform |
|---|---|---|
| `dev` | Desenvolvimento local (Docker Compose) | — |
| `staging` | Validação automatizada | `staging` |
| `prod` | Produção | `default` |

## 2.1 Repositório configurado

- **URL:** https://github.com/EdsonOliveira18/chassiscan
- Visibilidade pública, licença MIT, `.gitignore` para Python/Terraform.
- Branch `main` protegida: PR obrigatório e *status check* do CI exigido.

## 2.2 Workflow — `.github/workflows/ci.yml`

```yaml
name: CI

on:
  push:
    branches: [main, 'feature/**', 'fix/**']
  pull_request:
    branches: [main]
  workflow_dispatch:

env:
  PYTHON_DEFAULT: '3.11'

jobs:
  build-and-test:
    name: Build e Testes (Python ${{ matrix.python-version }})
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ['3.11', '3.12']

    steps:
      - name: Checkout do código
        uses: actions/checkout@v4

      - name: Configurar Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip

      - name: Instalar Tesseract OCR
        run: |
          sudo apt-get update
          sudo apt-get install -y tesseract-ocr

      - name: Instalar dependências
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install ruff pytest pytest-cov httpx

      - name: Lint (Ruff)
        run: |
          ruff check .
          ruff format --check .

      - name: Testes automatizados com cobertura
        run: pytest --cov=app --cov-report=term-missing --cov-report=html --cov-fail-under=80

      - name: Publicar relatório de cobertura
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: cobertura-py${{ matrix.python-version }}
          path: htmlcov/
          retention-days: 7

  docker:
    name: Build da imagem Docker
    runs-on: ubuntu-latest
    needs: build-and-test
    steps:
      - uses: actions/checkout@v4
      - name: Build da imagem
        run: docker build -t chassiscan:${{ github.sha }} .
      - name: Smoke test do container
        run: |
          docker run -d --name api -p 8000:8000 chassiscan:${{ github.sha }}
          sleep 8
          curl -f http://localhost:8000/health
          docker rm -f api

  terraform:
    name: Validação do IaC
    runs-on: ubuntu-latest
    needs: build-and-test
    defaults:
      run:
        working-directory: ./infra
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.9.5
      - name: Formatação
        run: terraform fmt -check -recursive
      - name: Inicialização
        run: terraform init -backend=false
      - name: Validação
        run: terraform validate
```

## 2.3 Scripts de build automatizados

**`Dockerfile`**

```dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update && \
    apt-get install -y --no-install-recommends tesseract-ocr libgl1 curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`** (ambiente de desenvolvimento)

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - OCR_LANG=eng
      - MAX_BYTES=10485760
    volumes:
      - ./app:/app/app
    restart: unless-stopped
```

**`Makefile`** (padronização dos comandos)

```makefile
.PHONY: install lint test build up down plan apply

install:
	pip install -r requirements.txt

lint:
	ruff check . --fix && ruff format .

test:
	pytest --cov=app --cov-report=term-missing --cov-fail-under=80

build:
	docker build -t chassiscan:local .

up:
	docker compose up -d

down:
	docker compose down

plan:
	cd infra && terraform init && terraform plan

apply:
	cd infra && terraform apply -auto-approve
```

## 2.4 Testes automatizados integrados

**`tests/test_vin_utils.py`**

```python
import pytest
from app.vin_utils import normalizar_vin, validar_vin, calcular_digito


def test_normaliza_caracteres_ambiguos():
    assert normalizar_vin("9BWZZZ377VT0O4251") == "9BWZZZ377VT004251"


@pytest.mark.parametrize("vin", ["1M8GDM9AXKP042788", "11111111111111111"])
def test_vin_valido(vin):
    assert validar_vin(vin) is True


def test_vin_invalido_por_checksum():
    assert validar_vin("1M8GDM9A1KP042788") is False


def test_vin_com_tamanho_incorreto():
    assert validar_vin("ABC123") is False


def test_digito_verificador_x():
    assert calcular_digito("1M8GDM9AXKP042788") == "X"
```

**`tests/test_api.py`**

```python
import io
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.api import app

cliente = TestClient(app)


def test_health_check():
    resposta = cliente.get("/health")
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "ok"


def test_arquivo_vazio_retorna_400():
    resposta = cliente.post("/ocr/chassi", files={"file": ("v.jpg", b"", "image/jpeg")})
    assert resposta.status_code == 400


def test_arquivo_grande_retorna_413():
    grande = b"0" * (10 * 1024 * 1024 + 1)
    resposta = cliente.post("/ocr/chassi", files={"file": ("g.jpg", grande, "image/jpeg")})
    assert resposta.status_code == 413


@patch("app.api.extrair_texto", return_value=("9BWZZZ377VT004251", 0.92))
def test_ocr_com_sucesso(_mock):
    imagem = io.BytesIO(b"fake-bytes")
    resposta = cliente.post("/ocr/chassi", files={"file": ("c.jpg", imagem, "image/jpeg")})
    assert resposta.status_code == 200
    assert resposta.json()["vin"] == "9BWZZZ377VT004251"
```

Execução local:

```bash
pytest --cov=app --cov-report=term-missing
```

O mesmo comando roda no CI (estágio 7), com `--cov-fail-under=80` — os testes são, portanto, **integrados ao pipeline**, não apenas locais.

---

## 3.1 Organização

```
infra/
├── main.tf         # Recursos: VPC, EC2, S3, IAM
├── variables.tf    # Variáveis de entrada
├── outputs.tf      # Saídas (IP, URL, bucket)
├── provider.tf     # Provider e backend
├── user_data.sh    # Provisionamento da instância
└── terraform.tfvars.example
```

## 3.2 `provider.tf`

```hcl
terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.60"
    }
  }

  # Backend remoto (descomentar após criar o bucket de state)
  # backend "s3" {
  #   bucket = "chassiscan-tfstate"
  #   key    = "prod/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Projeto   = "chassiscan"
      Ambiente  = var.ambiente
      Gerencia  = "terraform"
    }
  }
}
```

## 3.3 `variables.tf`

```hcl
variable "aws_region" {
  description = "Região AWS de provisionamento"
  type        = string
  default     = "us-east-1"
}

variable "ambiente" {
  description = "Nome do ambiente (dev, staging, prod)"
  type        = string
  default     = "prod"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.ambiente)
    error_message = "Ambiente deve ser dev, staging ou prod."
  }
}

variable "instance_type" {
  description = "Tipo da instância EC2"
  type        = string
  default     = "t3.micro"
}

variable "key_name" {
  description = "Nome do par de chaves SSH existente na AWS"
  type        = string
}

variable "ssh_cidr" {
  description = "CIDR autorizado a acessar a porta 22"
  type        = string
  default     = "0.0.0.0/32"
}

variable "vpc_cidr" {
  description = "CIDR da VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "subnet_cidr" {
  description = "CIDR da subnet pública"
  type        = string
  default     = "10.0.1.0/24"
}
```

## 3.4 `main.tf`

```hcl
# ---------- Rede ----------
resource "aws_vpc" "principal" {
  cidr_block           = var.vpc_cidr
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = { Name = "chassiscan-vpc-${var.ambiente}" }
}

resource "aws_internet_gateway" "gateway" {
  vpc_id = aws_vpc.principal.id
  tags   = { Name = "chassiscan-igw-${var.ambiente}" }
}

resource "aws_subnet" "publica" {
  vpc_id                  = aws_vpc.principal.id
  cidr_block              = var.subnet_cidr
  map_public_ip_on_launch = true
  availability_zone       = data.aws_availability_zones.disponiveis.names[0]

  tags = { Name = "chassiscan-subnet-publica-${var.ambiente}" }
}

resource "aws_route_table" "publica" {
  vpc_id = aws_vpc.principal.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gateway.id
  }

  tags = { Name = "chassiscan-rt-publica-${var.ambiente}" }
}

resource "aws_route_table_association" "publica" {
  subnet_id      = aws_subnet.publica.id
  route_table_id = aws_route_table.publica.id
}

# ---------- Segurança ----------
resource "aws_security_group" "api" {
  name        = "chassiscan-sg-${var.ambiente}"
  description = "Libera acesso HTTP a API e SSH restrito"
  vpc_id      = aws_vpc.principal.id

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "API FastAPI"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH administrativo"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "chassiscan-sg-${var.ambiente}" }
}

# ---------- Armazenamento ----------
resource "random_id" "sufixo" {
  byte_length = 4
}

resource "aws_s3_bucket" "imagens" {
  bucket = "chassiscan-imagens-${var.ambiente}-${random_id.sufixo.hex}"
}

resource "aws_s3_bucket_versioning" "imagens" {
  bucket = aws_s3_bucket.imagens.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "imagens" {
  bucket = aws_s3_bucket.imagens.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "imagens" {
  bucket                  = aws_s3_bucket.imagens.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ---------- IAM (menor privilégio) ----------
resource "aws_iam_role" "ec2" {
  name = "chassiscan-ec2-role-${var.ambiente}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "s3" {
  name = "chassiscan-s3-policy"
  role = aws_iam_role.ec2.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
      Resource = [aws_s3_bucket.imagens.arn, "${aws_s3_bucket.imagens.arn}/*"]
    }]
  })
}

resource "aws_iam_instance_profile" "ec2" {
  name = "chassiscan-profile-${var.ambiente}"
  role = aws_iam_role.ec2.name
}

# ---------- Computação ----------
data "aws_availability_zones" "disponiveis" {
  state = "available"
}

data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-x86_64"]
  }
}

resource "aws_instance" "api" {
  ami                    = data.aws_ami.amazon_linux.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.publica.id
  vpc_security_group_ids = [aws_security_group.api.id]
  key_name               = var.key_name
  iam_instance_profile   = aws_iam_instance_profile.ec2.name

  user_data = templatefile("${path.module}/user_data.sh", {
    bucket = aws_s3_bucket.imagens.bucket
  })

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
    encrypted   = true
  }

  tags = { Name = "chassiscan-api-${var.ambiente}" }
}
```

## 3.5 `user_data.sh` — provisionamento da instância

```bash
#!/bin/bash
set -euo pipefail

dnf update -y
dnf install -y docker git
systemctl enable --now docker
usermod -aG docker ec2-user

echo "BUCKET_IMAGENS=${bucket}" >> /etc/environment

docker run -d \
  --name chassiscan \
  --restart unless-stopped \
  -p 8000:8000 \
  -e BUCKET_IMAGENS=${bucket} \
  ghcr.io/USUARIO/chassiscan:latest
```

## 3.6 `outputs.tf`

```hcl
output "ip_publico" {
  description = "IP público da instância da API"
  value       = aws_instance.api.public_ip
}

output "url_api" {
  description = "URL base da API"
  value       = "http://${aws_instance.api.public_dns}:8000"
}

output "url_documentacao" {
  description = "Documentação Swagger"
  value       = "http://${aws_instance.api.public_dns}:8000/docs"
}

output "bucket_imagens" {
  description = "Nome do bucket S3"
  value       = aws_s3_bucket.imagens.bucket
}
```

## 3.7 Execução do IaC

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars   # preencher key_name e ssh_cidr

terraform init          # baixa providers e inicializa o state
terraform fmt -recursive
terraform validate      # valida a sintaxe
terraform plan          # revisa o que será criado
terraform apply         # provisiona
terraform output        # exibe IP e URLs
terraform destroy       # remove tudo (evita custos)
```

---

## 4. Estrutura completa do repositório

```
chassiscan/
├── app/
│   ├── __init__.py
│   ├── api.py              # Rotas HTTP e validações
│   ├── ocr_engine.py       # Pré-processamento e OCR
│   └── vin_utils.py        # Regras de negócio do VIN
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   └── test_vin_utils.py
├── infra/
│   ├── provider.tf
│   ├── main.tf
│   ├── variables.tf
│   ├── outputs.tf
│   ├── user_data.sh
│   └── terraform.tfvars.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── docs/
│   └── evidencias/         # Prints do pipeline e do terraform apply
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── requirements.txt
├── pyproject.toml          # Configuração do Ruff e Pytest
├── .env.example
├── .gitignore
├── LICENSE
└── README.md
```

---

## 5. Como executar o projeto

```bash
# Clonar
git clone https://github.com/USUARIO/chassiscan.git
cd chassiscan

# Opção A — Docker (recomendado)
docker compose up -d
# API disponível em http://localhost:8000/docs

# Opção B — Ambiente virtual Python
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.api:app --reload
```

**Teste rápido:**

```bash
curl -X POST http://127.0.0.1:8000/ocr/chassi -F "file=@exemplos/chassi.jpg"
```

---

## 6. Endpoints

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/health` | Verificação de disponibilidade |
| `POST` | `/ocr/chassi` | Extrai e valida o VIN de uma imagem |
| `GET` | `/docs` | Documentação Swagger UI |

Resposta de `POST /ocr/chassi`:

```json
{
  "vin": "9BWZZZ377VT004251",
  "valido": true,
  "confianca": 0.92,
  "texto_bruto": "9BWZZZ377VT0O4251"
}
```

| Código | Situação |
|---|---|
| 200 | Processado com sucesso |
| 400 | Arquivo vazio |
| 413 | Arquivo maior que 10 MB |
| 415 | Formato de imagem inválido |
| 500 | Erro interno no processamento |

## 7. Próximas fases

- [ ] Publicar imagem no GHCR e automatizar o *deploy* (CD).
- [ ] Backend remoto do Terraform com *lock* no DynamoDB.
- [ ] Monitoramento e alertas (CloudWatch / Prometheus).
- [ ] Autenticação por API key.

## 8. Referências

- ISO 3779:2009 — *Road vehicles: Vehicle Identification Number (VIN)*
- GitHub Actions — https://docs.github.com/actions
- Terraform AWS Provider — https://registry.terraform.io/providers/hashicorp/aws/latest/docs
- FastAPI — https://fastapi.tiangolo.com
- Tesseract OCR — https://github.com/tesseract-ocr/tesseract
- Pytest — https://docs.pytest.org
- Ruff — https://docs.astral.sh/ruff
*Desenvolvido por **Edson** — Análise e Desenvolvimento de Sistemas · Disciplina de DevOps · Fase 1*
