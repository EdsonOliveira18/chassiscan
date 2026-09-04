# ---------------------------------------------------------------
# ChassiScan — recursos de infraestrutura
# Providers e versoes: ver providers.tf
# ---------------------------------------------------------------

locals {
  name_prefix = "${var.project}-${var.env}"
}

# ---------------------------------------------------------------
# Bucket para as imagens de chassi enviadas pelo app
# ---------------------------------------------------------------
resource "aws_s3_bucket" "images" {
  bucket        = "${local.name_prefix}-images"
  force_destroy = var.env != "prod"
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
    bucket_key_enabled = true
  }
}

resource "aws_s3_bucket_public_access_block" "images" {
  bucket = aws_s3_bucket.images.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Bloqueia qualquer acesso fora de TLS
resource "aws_s3_bucket_policy" "images_tls_only" {
  bucket = aws_s3_bucket.images.id
  policy = data.aws_iam_policy_document.images_tls_only.json

  depends_on = [aws_s3_bucket_public_access_block.images]
}

data "aws_iam_policy_document" "images_tls_only" {
  statement {
    sid    = "DenyInsecureTransport"
    effect = "Deny"

    principals {
      type        = "*"
      identifiers = ["*"]
    }

    actions = ["s3:*"]

    resources = [
      aws_s3_bucket.images.arn,
      "${aws_s3_bucket.images.arn}/*",
    ]

    condition {
      test     = "Bool"
      variable = "aws:SecureTransport"
      values   = ["false"]
    }
  }
}

# Expurgo automatico — atende ao principio de retencao minima (LGPD)
resource "aws_s3_bucket_lifecycle_configuration" "images" {
  bucket = aws_s3_bucket.images.id

  rule {
    id     = "expire-images"
    status = "Enabled"

    filter {}

    expiration {
      days = var.retention_days
    }

    noncurrent_version_expiration {
      noncurrent_days = 1
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  depends_on = [aws_s3_bucket_versioning.images]
}

# ---------------------------------------------------------------
# Registro da imagem Docker do ChassiScan
# ---------------------------------------------------------------
resource "aws_ecr_repository" "api" {
  name                 = local.name_prefix
  image_tag_mutability = var.env == "prod" ? "IMMUTABLE" : "MUTABLE"
  force_delete         = var.env != "prod"

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }
}

resource "aws_ecr_lifecycle_policy" "api" {
  repository = aws_ecr_repository.api.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Manter apenas as 10 imagens mais recentes"
        selection = {
          tagStatus   = "any"
          countType   = "imageCountMoreThan"
          countNumber = 10
        }
        action = { type = "expire" }
      },
    ]
  })
}

# ---------------------------------------------------------------
# Observabilidade
# ---------------------------------------------------------------
resource "aws_cloudwatch_log_group" "api" {
  name              = "/${var.project}/${var.env}/api"
  retention_in_days = var.log_retention_days
}

resource "aws_cloudwatch_log_metric_filter" "ocr_failures" {
  name           = "${local.name_prefix}-ocr-failures"
  log_group_name = aws_cloudwatch_log_group.api.name
  pattern        = "?ERROR ?checksum"

  metric_transformation {
    name          = "OcrFailures"
    namespace     = "ChassiScan/${var.env}"
    value         = "1"
    default_value = "0"
  }
}

resource "aws_cloudwatch_metric_alarm" "ocr_failures" {
  alarm_name          = "${local.name_prefix}-ocr-failures"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  threshold           = var.ocr_failure_threshold
  period              = 300
  statistic           = "Sum"
  namespace           = "ChassiScan/${var.env}"
  metric_name         = aws_cloudwatch_log_metric_filter.ocr_failures.metric_transformation[0].name
  treat_missing_data  = "notBreaching"
  alarm_description   = "Falhas de OCR/checksum acima do esperado em 5 minutos"
}
