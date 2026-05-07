variable "stackit_project_id" {
  description = "STACKIT project identifier."
  type        = string
}

variable "stackit_region" {
  description = "STACKIT region for all resources."
  type        = string
  default     = "eu01"
}

variable "rabbitmq_instance_name" {
  description = "Canonical RabbitMQ instance name."
  type        = string
}

variable "rabbitmq_version" {
  description = "RabbitMQ major version."
  type        = string
  default     = "4.0"
}

variable "rabbitmq_plan_name" {
  description = "STACKIT RabbitMQ service plan name."
  type        = string
  default     = "stackit-rabbitmq-2.4.10-replica"
}
