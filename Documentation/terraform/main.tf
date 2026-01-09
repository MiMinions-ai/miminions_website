provider "aws" {
  region     = var.region
  access_key = var.access_key
  secret_key = var.secret_key
  token      = var.aws_session_token
}

resource "aws_security_group" "Miminions" {
  name_prefix = "Miminions-"
  description = "Allow inbound traffic for web and DB"
  vpc_id      = var.vpc_id

  ingress {
    description = "Allow HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "Allow custom port 5010"
    from_port   = 5010
    to_port     = 5010
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "Miminions"
  }
}

data "aws_ami" "amazon_linux_2023_arm" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-*-arm64"]
  }

  filter {
    name   = "architecture"
    values = ["arm64"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "Miminions" {
  ami                    = var.ami_id
  instance_type          = var.instance_type
  subnet_id              = var.subnet_id
  vpc_security_group_ids = [aws_security_group.Miminions.id]
  key_name               = var.key_name

   root_block_device {
    volume_size = 20       # Set root volume to 20 GB
    volume_type = "gp3"    # General Purpose SSD (you can change to gp2, io1, etc.)
  }

  tags = {
    Name = "Miminions"
  }
}

resource "aws_s3_bucket" "miminions" {
  bucket = var.bucket_name

  tags = {
    Name = "miminions"
  }

  lifecycle {
    prevent_destroy = false
  }
  force_destroy = true
}

resource "aws_s3_bucket_ownership_controls" "miminions_ownership" {
  bucket = aws_s3_bucket.miminions.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_dynamodb_table" "miminions" {
  name           = var.dynamodb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name = "miminions"
  }
}
