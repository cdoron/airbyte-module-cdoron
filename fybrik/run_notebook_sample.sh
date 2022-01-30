#!/bin/bash

if [ -z "$FYBRIK_DIR" ]
  then echo "FYBRIK_DIR is blank. Set FYBRIK_DIR and run again"
  exit
fi

kind delete cluster
kind create cluster

# get started
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

# customize taxonomy to support 
go run main.go taxonomy compile --out custom-taxonomy.json --base charts/fybrik/files/taxonomy/taxonomy.json $AIRBYTE_FYBRIK/fybrik-taxonomy-patch.yaml

helm install fybrik charts/fybrik --set global.tag=master --set global.imagePullPolicy=Always -n fybrik-system --wait --set-file taxonomyOverride=custom-taxonomy.json

kubectl apply -f $AIRBYTE_FYBRIK/../module.yaml -n fybrik-system
