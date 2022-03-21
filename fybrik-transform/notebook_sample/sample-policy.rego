package dataapi.authz

rule[{"action": {"name":"AgeFilterAction", "options": {"age": age}, "columns": column_names}, "policy": description}] {
  description := "Apply AgeFilter to datasets tagged with finance = true"
  age := 20
  column_names := ["Date of Birth"]
  input.action.actionType == "read"
  input.resource.metadata.tags.finance
}
