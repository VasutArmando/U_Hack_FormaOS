terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

variable "project_id" {
  description = "ID-ul proiectului Google Cloud"
  type        = string
  default     = "forma-os-hackathon"
}

variable "region" {
  description = "Regiunea principală pentru Cloud Run"
  default     = "europe-west4"
}

# 1. Serviciul Backend Cloud Run (Serverless FastAPI)
resource "google_cloud_run_v2_service" "forma_os_api" {
  name     = "forma-os-backend"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    containers {
      image = "gcr.io/${var.project_id}/forma-os-backend:latest"
      
      resources {
        limits = {
          cpu    = "1000m"
          memory = "2048Mi" # 2GB RAM e perfect pentru procesarea imaginilor/matricei
        }
      }
      
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
    
    # Menținem mereu o instanță caldă (Warm Start) pentru a garanta latență sub 100ms
    scaling {
      min_instance_count = 1
      max_instance_count = 10
    }
  }
}

# 2. Setăm acces public (neautentificat) pentru aplicația Flutter web
resource "google_cloud_run_service_iam_member" "public_access" {
  location = google_cloud_run_v2_service.forma_os_api.location
  project  = google_cloud_run_v2_service.forma_os_api.project
  service  = google_cloud_run_v2_service.forma_os_api.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# 3. Infrastructura Datelor: Dataset BigQuery ML pentru SHIELD Module
resource "google_bigquery_dataset" "forma_os_dataset" {
  dataset_id                  = "forma_os_ml_models"
  friendly_name               = "FORMA OS Data Pipeline"
  description                 = "Găzduiește modelele de Regresie Logistică antrenate direct în BQ"
  location                    = "EU"
  default_table_expiration_ms = 31536000000 # Date expirabile la 1 an pentru compliance
}
