output "images_bucket" {
  description = "Bucket S3 onde as imagens de chassi são armazenadas"
  value       = aws_s3_bucket.images.bucket
}

output "ecr_repository_url" {
  description = "URL do repositório ECR para push da imagem Docker"
  value       = aws_ecr_repository.api.repository_url
}

output "log_group_name" {
  description = "Log group do CloudWatch usado pela API"
  value       = aws_cloudwatch_log_group.api.name
}
