python3 ./lambda/stop.py
python3 ./lambda/s3_destroyer.py
python3 ./lambda/ecr_destroyer.py
python3 ./lambda/ami_destroyer.py

terraform -chdir=./terraform/ destroy -auto-approve

rm ./terraform/variables.tf
rm ./lambda/const_config.py
