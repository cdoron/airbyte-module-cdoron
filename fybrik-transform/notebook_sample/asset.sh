export POSTGRES_PASSWORD=$(kubectl get secret --namespace default my-postgres-postgresql -o jsonpath="{.data.postgres-password}" | base64 --decode)

cat << EOF | kubectl apply -f -
apiVersion: katalog.fybrik.io/v1alpha1
kind: Asset
metadata:
  name: postgres-asset
spec:
  secretRef: 
    name: postgres-asset
  details:
    dataFormat: csv
    connection:
      name: postgres
      postgres:
        connector: "airbyte/source-postgres"
        host: "my-postgres-postgresql.default"
        port: "5432"
        database: "postgres"
        username: "postgres"
        password: "$POSTGRES_PASSWORD"
        ssl: false
  metadata:
    name: test data
    geography: theshire 
    tags:
      finance: true
EOF
