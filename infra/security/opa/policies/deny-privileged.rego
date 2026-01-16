# OPA Policy: Deny Privileged Containers
# No privileged containers allowed

package kubernetes.admission

import future.keywords.in

# Deny privileged containers
deny[msg] {
    input.request.kind.kind == "Pod"
    container := input.request.object.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container %s in Pod %s cannot run as privileged", [container.name, input.request.object.metadata.name])
}

deny[msg] {
    input.request.kind.kind == "Deployment"
    container := input.request.object.spec.template.spec.containers[_]
    container.securityContext.privileged == true
    msg := sprintf("Container %s in Deployment %s cannot run as privileged", [container.name, input.request.object.metadata.name])
}

# Deny hostNetwork
deny[msg] {
    input.request.kind.kind == "Pod"
    input.request.object.spec.hostNetwork == true
    msg := sprintf("Pod %s cannot use hostNetwork", [input.request.object.metadata.name])
}

# Deny hostPID
deny[msg] {
    input.request.kind.kind == "Pod"
    input.request.object.spec.hostPID == true
    msg := sprintf("Pod %s cannot use hostPID", [input.request.object.metadata.name])
}
