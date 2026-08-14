variable "region" {
  description = "Região AWS (São Paulo, para manter os dados no Brasil)"
  type        = string
  default     = "sa-east-1"
}

variable "project" {
  description = "Nome do projeto, usado como prefixo dos recursos"
  type        = string
  default     = "chassiscan"
}

variable "env" {
  description = "Ambiente de implantação"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "hml", "prod"], var.env)
    error_message = "O ambiente deve ser dev, hml ou prod."
  }
}

variable "retention_days" {
  description = "Dias de retenção das imagens no S3"
  type        = number
  default     = 90

  validation {
    condition     = var.retention_days > 0 && var.retention_days <= 365
    error_message = "A retenção deve estar entre 1 e 365 dias."
  }
}
