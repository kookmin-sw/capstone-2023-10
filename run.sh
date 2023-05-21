#!/bin/bash

cred=$(cat ~/.aws/credentials | grep default)

if [ -z $cred ]; then
  echo "Configure Your AWS Account"
  aws configure
fi

echo Please enter the Region[AWS] where the system will run: 
read region_name

echo Please enter the System Name: 
read system_prefix

echo Please enter the instance type for which you want the system to run
read instance_type

cat << EOF > ./terraform/variables.tf
variable "region" {
  type = string
  description = "Input Your AWS Region"
  default = "$region_name"
}

variable "prefix" {
  type = string
  description = "Input Your System Name"
  default = "$system_prefix"
}

EOF

cat << EOF > ./lambda/const_config.py
## << AWS >>
### Your Account Profile in Your AWS-CLI
AWS_PROFILE_NAME = "default"
AWS_REGION_NAME = "$region_name"
START_INSTANCE_TYPE = "$instance_type"
## << GCP >>
### ...
## << AZURE >>
### ...
## << COMMON >>
SYSTEM_PREFIX = "$system_prefix"

EOF

# Detect the operating system
OS=$(uname -s)

if [ "$OS" = "Darwin" ]; then
  # MacOS
  if [[ $(command -v brew) = "" ]]; then
    sudo /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  fi
  sudo brew update
  sudo brew install python@3.10
  sudo pip install -r pip_requirements.txt
  sudo brew install hashicorp/tap/terraform@1.4.5

elif [ "$OS" = "Linux" ]; then
  # Ubuntu or RedHat
  if [ -f "/etc/lsb-release" ]; then
    # Ubuntu
    sudo apt-get update
    sudo apt-get install python3.10
    sudo pip install -r pip_requirements.txt
    sudo apt-get install -y wget unzip
    sudo wget https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_linux_amd64.zip
    sudo unzip terraform_1.4.5_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
  elif [ -f "/etc/redhat-release" ]; then
    # RedHat
    sudo yum update
    sudo yum install python310
    sudo pip install -r pip_requirements.txt
    sudo yum install -y wget unzip
    sudo wget https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_linux_amd64.zip
    sudo unzip terraform_1.4.5_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
  fi

else
  echo "Unsupported operating system: $OS"
  exit 1
fi
# elif [ "$OS" = "Windows_NT" ]; then
#   # Windows
#   $PYTHON_URL = "https://www.python.org/ftp/python/3.9.2/python-3.9.2-amd64.exe"
#   $INSTALLER = "python-3.9.2-amd64.exe"
#   $TEMP_DIR = "$($env:TEMP)\$($INSTALLER)"

#   Invoke-WebRequest -Uri $PYTHON_URL -OutFile $TEMP_DIR & $TEMP_DIR /quiet InstallAllUsers=1 PrependPath=1

#   Remove-Item $TEMP_DIR
  
#   pip install -r pip_requirements.txt

#   $TERRAFORM_URL = "https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_windows_amd64.zip"
#   $ZIP_FILE = "terraform_1.4.5_windows_amd64.zip"
#   $TEMP_DIR = "$($env:TEMP)\$($ZIP_FILE)"

#   Invoke-WebRequest -Uri $TERRAFORM_URL -OutFile $TEMP_DIR

#   Add-Type -AssemblyName System.IO.Compression.FileSystem
#   [System.IO.Compression.ZipFile]::ExtractToDirectory($TEMP_DIR, "$($env:TEMP)\terraform")

#   Move-Item "$($env:TEMP)\terraform\terraform.exe" "C:\Windows\System32\terraform.exe"

#   Remove-Item $TEMP_DIR
#   Remove-Item -Recurse "$($env:TEMP)\terraform"




zip -j ./terraform/jupyter-main-worker.zip ./lambda/migrations/lambda_function.py ./lambda/const_config.py
zip -j ./terraform/model-function.zip ./lambda/const_config.py
cd ./lambda/models/
zip -r ../../terraform/model-function.zip *
cd ../../

terraform -chdir=./terraform/ init
terraform -chdir=./terraform/ apply -auto-approve

rm ./terraform/jupyter-main-worker.zip
rm ./terraform/model-function.zip

python3 ./lambda/migrations/lambda_function.py
python3 ./lambda/models/lambda_function.py

