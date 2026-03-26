output "bootstrap_contract" {
  description = "Bootstrap metadata contract used by downstream automation."
  value       = terraform_data.bootstrap_contract.input
}

output "foundation_state_key" {
  description = "Deterministic remote state object key for foundation layer."
  value       = terraform_data.bootstrap_contract.input.foundation_state
}
