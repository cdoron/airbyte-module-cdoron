helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-postgres bitnami/postgresql

export POSTGRES_PASSWORD=$(kubectl get secret --namespace default my-postgres-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)


