package dataapi.authz

rule[{"action": {"name":"FilterAction", "options": {"query": query}}, "policy": description}] {
  description := "Apply Filter to datasets tagged with finance = true"
  query := "Country == 'Israel' or Country == 'United Kingdom'"
  input.action.actionType == "read"
  input.resource.metadata.tags.finance
}
