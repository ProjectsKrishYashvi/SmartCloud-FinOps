terraform {
  required_version = ">= 1.4.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region = var.region
}

variable "region" { type = string }
variable "project" {
  type    = string
  default = "smartcloud-finops"
}
variable "tenant"  { 
  type = string  
  default = "tenantA" 
}

resource "aws_key_pair" "this" {
  key_name   = "${var.project}-${var.tenant}-key"
  public_key = file(var.public_key_path)
}

variable "public_key_path" { type = string }

resource "aws_security_group" "sg" {
  name        = "${var.project}-${var.tenant}-sg"
  description = "Allow SSH and HTTP"
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  ingress {
    from_port   = 80
    to_port     = 80
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
    Project = var.project
    Tenant  = var.tenant
  }
}

# Free-tier eligible AMI lookup (Amazon Linux 2)
data "aws_ami" "al2" {
  most_recent = true
  owners      = ["amazon"]
  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }
}

resource "aws_instance" "vm" {
  ami                    = data.aws_ami.al2.id
  instance_type          = "t3.micro"
  key_name               = aws_key_pair.this.key_name
  vpc_security_group_ids = [aws_security_group.sg.id]
  user_data              = <<-EOF
              #!/bin/bash
              yum update -y
              amazon-linux-extras install epel -y || true
              yum install -y python3 git
              echo "Hello from ${var.tenant}/AWS" > /var/www/html/index.html
              yum install -y httpd
              systemctl enable httpd
              systemctl start httpd
              EOF
  tags = {
    Name    = "${var.project}-${var.tenant}-vm"
    Project = var.project
    Tenant  = var.tenant
  }
}

output "public_ip" {
  value = aws_instance.vm.public_ip
}
output "public_dns" {
  value = aws_instance.vm.public_dns
} 