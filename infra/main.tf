terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.region

  default_tags {
    tags = {
      Project   = var.project
      Env       = var.env
      ManagedBy = "Terraform"
    }
  }
}

# ---------------------------------------------------------------
# Bucket para as imagens de chassi enviadas pelo app
# ---------------------------------------------------------------
resource "aws_s3_bucket" "images" {
  bucket = "${var.project}-images-${var.env}"
}

resource "aws_s3_bucket_versioning" "images" {
  bucket = aws_s3_bucket.images.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Expurgo automático — atende ao princípio de retenção mínima (LGPD)
resource "aws_s3_bucket_lifecycle_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    id     = "expire-images"
    status = "Enabled"

    filter {}

    expiration {
      days = var.retention_days
    }
  }
}

# ---------------------------------------------------------------
# Registro da imagem Docker do ChassiScan
# ---------------------------------------------------------------
resource "aws_ecr_repository" "api" {
  name                 = var.project
  image_tag_mutability = "MUTABLE"
  force_delete         = var.env != "prod"

  image_scanning_configuration {
    scan_on_push = true
  }
}

# ---------------------------------------------------------------
# Observabilidade
# ---------------------------------------------------------------
resource "aws_cloudwatch_log_group" "api" {
  name              = "/${var.project}/api"
  retention_in_days = 14
}

resource "aws_cloudwatch_log_metric_filter" "ocr_failures" {
  name           = "${var.project}-ocr-failures"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "?ERROR ?checksum"

  metric_transformation {
    name      = "OcrFailures"
    namespace = var.project
    value     = "1"
  }
}
