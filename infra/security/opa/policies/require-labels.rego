# OPA Policy: Require Labels
# All Kubernetes resources must have required labels

package kubernetes.admission

import future.keywords.in

# Required labels for all resources
required_labels := ["team", "environment", "managed-by"]

# Deny if missing required labels
deny[msg] {
    input.request.kind.kind == "Deployment"
    labels := input.request.object.metadata.labels
    missing := {label | label := required_labels[_]; not labels[label]}
    count(missing) > 0
    msg := sprintf("Deployment %s is missing required labels: %v", [input.request.object.metadata.name, missing])
}

deny[msg] {
    input.request.kind.kind == "Service"
    labels := input.request.object.metadata.labels
    missing := {label | label := required_labels[_]; not labels[label]}
    count(missing) > 0
    msg := sprintf("Service %s is missing required labels: %v", [input.request.object.metadata.name, missing])
}
