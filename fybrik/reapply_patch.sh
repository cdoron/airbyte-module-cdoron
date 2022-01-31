#!/bin/bash

if [ -z "$FYBRIK_DIR" ]
  then echo "FYBRIK_DIR is blank. Set FYBRIK_DIR and run again"
  exit
fi

export AIRBYTE_FYBRIK=$PWD
cd $FYBRIK_DIR

helm delete fybrik -n fybrik-system

# customize taxonomy to support 
go run main.go taxonomy compile --out custom-taxonomy.json --base charts/fybrik/files/taxonomy/taxonomy.json $AIRBYTE_FYBRIK/fybrik-taxonomy-patch.yaml

helm install fybrik charts/fybrik --set global.tag=master --set global.imagePullPolicy=Always -n fybrik-system --wait --set-file taxonomyOverride=custom-taxonomy.json

