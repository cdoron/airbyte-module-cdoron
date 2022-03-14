package dataapi.authz

rule[{"action": {"name":"FilterAction", "options": {"query": "Country == 'Israel' or Country == 'United Kingdom'"}}, "policy": description}] {
  description := "Apply Filter to datasets tagged with finance = true"
  input.action.actionType == "read"
  input.resource.metadata.tags.finance
}
