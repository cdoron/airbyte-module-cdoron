helm repo add bitnami https://charts.bitnami.com/bitnami
helm install my-postgres bitnami/postgresql --wait

export POSTGRES_PASSWORD=$(kubectl get secret --namespace default my-postgres-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)

kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "CREATE TABLE users(id SERIAL PRIMARY KEY, col1 VARCHAR(200));"
kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "INSERT INTO public.users(col1) VALUES('record1');"
kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "INSERT INTO public.users(col1) VALUES('record2');"
kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "INSERT INTO public.users(col1) VALUES('record3');"

kubectl run my-postgres-postgresql-client --rm --tty -i --restart='Never' --namespace default --image docker.io/bitnami/postgresql:11.14.0-debian-10-r28 --env="PGPASSWORD=$POSTGRES_PASSWORD" --command -- psql --host my-postgres-postgresql -U postgres -d postgres -p 5432 -c "SELECT * FROM public.users;"
