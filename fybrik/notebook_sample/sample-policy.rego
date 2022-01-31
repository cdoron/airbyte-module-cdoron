package dataapi.authz

rule[{}] {
  input.action.actionType == "read"
  input.resource.metadata.tags.finance
}
