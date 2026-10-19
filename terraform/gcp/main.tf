terraform {
  required_version = ">= 1.4.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
  zone    = var.zone
}

variable "project" {
  type = string
}

variable "region" {
  type    = string
  default = "us-central1"
}

variable "zone" {
  type    = string
  default = "us-central1-a"
}

variable "tenant" {
  type    = string
  default = "tenantA"
}

resource "google_compute_instance" "vm" {
  name         = "smartcloud-${lower(var.tenant)}-vm"
  machine_type = "e2-micro"
  zone         = var.zone

  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-11"
    }
  }

  network_interface {
    network = "default"
    access_config {}
  }

  metadata_startup_script = <<-EOT
    #!/bin/bash
    apt-get update -y
    apt-get install -y nginx
    echo "Hello from ${var.tenant}/GCP" > /var/www/html/index.nginx-debian.html
    systemctl enable nginx
    systemctl start nginx
  EOT

  labels = {
    project = "smartcloud-finops"
    tenant  = var.tenant
  }
}

output "public_ip" {
  value = google_compute_instance.vm.network_interface[0].access_config[0].nat_ip
}
