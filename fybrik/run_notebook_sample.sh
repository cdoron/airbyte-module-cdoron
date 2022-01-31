#!/bin/bash

if [ -z "$FYBRIK_DIR" ]
  then echo "FYBRIK_DIR is blank. Set FYBRIK_DIR and run again"
  exit
fi

kind delete cluster
kind create cluster

# let's begin by installing postgres in the default namespace

helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-postgres bitnami/postgresql --wait

# create table and fill it with a few values
export POSTGRES_PASSWORD=$(kubectl get secret --namespace default my-postgres-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)

kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "CREATE TABLE users(id SERIAL PRIMARY KEY, col1 VARCHAR(200));"
kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "INSERT INTO public.users(col1) VALUES('record1');"
kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "INSERT INTO public.users(col1) VALUES('record2');"
kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "INSERT INTO public.users(col1) VALUES('record3');"

# install fybrik
helm repo add jetstack https://charts.jetstack.io
helm repo add hashicorp https://helm.releases.hashicorp.com
helm repo add fybrik-charts https://fybrik.github.io/charts
helm repo update

helm install cert-manager jetstack/cert-manager \
    --namespace cert-manager \
    --version v1.2.0 \
    --create-namespace \
    --set installCRDs=true \
    --wait --timeout 120s

export AIRBYTE_FYBRIK=$PWD
cd $FYBRIK_DIR
helm dependency update charts/vault
helm install vault charts/vault --create-namespace -n fybrik-system \
    --set "vault.injector.enabled=false" \
    --set "vault.server.dev.enabled=true" \
    --values charts/vault/env/dev/vault-single-cluster-values.yaml
kubectl wait --for=condition=ready --all pod -n fybrik-system --timeout=120s

helm install fybrik-crd charts/fybrik-crd -n fybrik-system --wait

# customize taxonomy to support the airbyte module
go run main.go taxonomy compile --out custom-taxonomy.json --base charts/fybrik/files/taxonomy/taxonomy.json $AIRBYTE_FYBRIK/fybrik-taxonomy-patch.yaml

# helm install fybrik
helm install fybrik charts/fybrik --set global.tag=master --set global.imagePullPolicy=Always -n fybrik-system --wait --set-file taxonomyOverride=custom-taxonomy.json

# define airbyte FybrikModule
kubectl apply -f $AIRBYTE_FYBRIK/../module.yaml -n fybrik-system

# run a notebook-like example
kubectl create namespace fybrik-notebook-sample
kubectl config set-context --current --namespace=fybrik-notebook-sample

kubectl apply -f $AIRBYTE_FYBRIK/notebook_sample/secret.yaml
$AIRBYTE_FYBRIK/notebook_sample/asset.sh

kubectl -n fybrik-system create configmap sample-policy --from-file=$AIRBYTE_FYBRIK/notebook_sample/sample-policy.rego
kubectl -n fybrik-system label configmap sample-policy openpolicyagent.org/policy=rego
while [[ $(kubectl get cm sample-policy -n fybrik-system -o 'jsonpath={.metadata.annotations.openpolicyagent\.org/policy-status}') != '{"status":"ok"}' ]]; do echo "waiting for policy to be applied" && sleep 5; done

kubectl apply -f $AIRBYTE_FYBRIK/notebook_sample/application.yaml

echo "Now all the is left is to run an ubuntu pod and check that the airbyte"
echo "service works properly."
echo "Run:"
echo -e "\tkubectl run my-shell --rm -i --tty --image ubuntu -- bash"
echo "Then, from the shell, run:"
echo -e "\tapt-get update; apt-get install -y curl"
echo -e "\tcurl -X GET my-notebook-fybrik-notebook-sample-airbyte-module.fybrik-blueprints/fybrik-notebook-sample/postgres-asset"
