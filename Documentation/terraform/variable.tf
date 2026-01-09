variable "region" {
  description = "AWS region"
  default     = "us-east-2"
}

variable "access_key" {
  description = "AWS Access Key"
  type        = string
  sensitive   = true
}

variable "secret_key" {
  description = "AWS Secret Key"
  type        = string
  sensitive   = true
}

variable "aws_session_token" {
  description = "AWS temporary session token for authentication"
  type        = string
  sensitive   = true
}

variable "bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
}

variable "vpc_id" {
  description = "The VPC ID where the instance will be launched"
  type        = string
}

variable "subnet_id" {
  description = "The Subnet ID where the EC2 instance will be launched"
  type        = string
}

variable "ami_id" {
  description = "The AMI ID to use for the EC2 instance"
  type        = string
}

variable "instance_type" {
  description = "The EC2 instance type"
  type        = string
  default     = "t2.micro"
}

variable "key_name" {
  description = "The key pair name for SSH access"
  type        = string
}

variable "dynamodb_table_name" {
  description = "The name of the DynamoDB table"
  type        = string
}