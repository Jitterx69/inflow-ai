# OPA Policy: Require Resource Limits
# All containers must specify resource limits

package kubernetes.admission

import future.keywords.in

# Deny pods without resource limits
deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    not container.resources.limits.cpu
    msg := sprintf("Container %s in Pod %s must specify CPU limits", [container.name, input.request.object.metadata.name])
}

deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    not container.resources.limits.memory
    msg := sprintf("Container %s in Pod %s must specify memory limits", [container.name, input.request.object.metadata.name])
}

deny[msg] {
    input.request.kind.kind == "Deployment"
    container := input.request.object.spec.template.spec.containers[_]
    not container.resources.limits.cpu
    msg := sprintf("Container %s in Deployment %s must specify CPU limits", [container.name, input.request.object.metadata.name])
}

deny[msg] {
    input.request.kind.kind == "Deployment"
    container := input.request.object.spec.template.spec.containers[_]
    not container.resources.limits.memory
    msg := sprintf("Container %s in Deployment %s must specify memory limits", [container.name, input.request.object.metadata.name])
}
