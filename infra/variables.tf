# ---------------------------------------------------------------
# ChassiScan — variaveis de entrada
# ---------------------------------------------------------------

variable "project" {
  description = "Nome curto do projeto, usado como prefixo dos recursos."
  type        = string
  default     = "chassiscan"

  validation {
    condition     = can(regex("^[a-z0-9-]{3,20}$", var.project))
    error_message = "Use apenas minusculas, numeros e hifen (3 a 20 caracteres)."
  }
}

variable "env" {
  description = "Ambiente de implantacao."
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.env)
    error_message = "env deve ser dev, staging ou prod."
  }
}

variable "region" {
  description = "Regiao AWS de destino."
  type        = string
  default     = "sa-east-1"
}

variable "retention_days" {
  description = "Dias de retencao das imagens de chassi no S3 (retencao minima - LGPD)."
  type        = number
  default     = 30

  validation {
    condition     = var.retention_days >= 1 && var.retention_days <= 365
    error_message = "retention_days deve estar entre 1 e 365."
  }
}

variable "log_retention_days" {
  description = "Dias de retencao dos logs no CloudWatch."
  type        = number
  default     = 14

  validation {
    condition = contains(
      [1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653],
      var.log_retention_days
    )
    error_message = "Valor nao aceito pelo CloudWatch Logs (ex.: 1, 3, 7, 14, 30, 90, 365)."
  }
}

variable "ocr_failure_threshold" {
  description = "Falhas de OCR/checksum em 5 minutos que disparam o alarme."
  type        = number
  default     = 10

  validation {
    condition     = var.ocr_failure_threshold > 0
    error_message = "ocr_failure_threshold deve ser maior que zero."
  }
}
