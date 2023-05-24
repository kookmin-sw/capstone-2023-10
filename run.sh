#!/bin/bash

cred=$(cat ~/.aws/credentials | grep default)

if [ -z $cred ]; then
  echo "Configure Your AWS Account"
  aws configure
fi

echo Please enter the Region[AWS] where the system will run: 
read -r -p "    " region_name
echo

echo Please enter the System Name: 
read -r -p "    " system_prefix
echo

echo Please enter the instance type for which you want the system to run
read -r -p "    " instance_type
echo

cat << EOF > ./lambda/const_config.py
## << AWS >>
### Your Account Profile in Your AWS-CLI
AWS_PROFILE_NAME = "default"
AWS_REGION_NAME = "$region_name"
START_VENDOR = "AWS"
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
  brew update
  brew upgrade
  brew install python@3.10
  sudo pip3 install -r pip_requirements.txt
  brew install hashicorp/tap/terraform

elif [ "$OS" = "Linux" ]; then
  # Ubuntu or RedHat
  if [ -f "/etc/lsb-release" ]; then
    # Ubuntu
    sudo apt update -y
    sudo apt install python3.10 -y
    sudo pip install -r pip_requirements.txt
    sudo apt-get install -y wget unzip
    sudo wget https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_linux_amd64.zip
    sudo unzip terraform_1.4.5_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
  elif [ -f "/etc/redhat-release" ]; then
    # RedHat
    sudo yum update -y
    sudo yum install python310 -y
    sudo pip3 install -r pip_requirements.txt
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
#   pip install torch==2.0.1 -t ./lambda/torch_layer/
#   pip install scikit-learn==1.2.2 -t ./lambda/scikit_learn_layer/
#   rm -r ./lambda/scikit_learn_layer/numpy*
#   pip install pandas==2.0.1 -t ./lambda/pandas_layer/
#   pip install numpy==1.24.3 -t ./lambda/numpy_layer/

#   $TERRAFORM_URL = "https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_windows_amd64.zip"
#   $ZIP_FILE = "terraform_1.4.5_windows_amd64.zip"
#   $TEMP_DIR = "$($env:TEMP)\$($ZIP_FILE)"

#   Invoke-WebRequest -Uri $TERRAFORM_URL -OutFile $TEMP_DIR

#   Add-Type -AssemblyName System.IO.Compression.FileSystem
#   [System.IO.Compression.ZipFile]::ExtractToDirectory($TEMP_DIR, "$($env:TEMP)\terraform")

#   Move-Item "$($env:TEMP)\terraform\terraform.exe" "C:\Windows\System32\terraform.exe"

#   Remove-Item $TEMP_DIR
#   Remove-Item -Recurse "$($env:TEMP)\terraform"


zip -j ./terraform/jupyter-main-worker.zip ./lambda/migrations/lambda_function.py ./lambda/migrations/waiter_manager.py ./lambda/const_config.py
zip -j ./model-function.zip ./lambda/const_config.py
cd ./lambda/models/
zip -r ../../model-function.zip *
cd ../../

echo Creating S3 Bucket...

system_check=$(python3 ./lambda/s3_creator.py)
RED='\033[0;31m'
NC='\033[0m'

if [ "$system_check" = "System name already exists" ]; then
  echo -e "${RED}[ERROR] ${NC}System Name already exists"
  exit 1

elif [ "$system_check" = "System has just been deleted" ]; then
  echo -e "${RED}[ERROR] ${NC}System has just been deleted"
  exit 1
fi

echo Creating Model Lambda Runtime...

ecr_image_uri=$(python3 ./lambda/ecr_creator.py)

echo "Model Lambda Runtime Image: $ecr_image_uri"

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

variable "image_uri" {
  type = string
  description = "Input Your ECR Image URI"
  default = "$ecr_image_uri"
}

EOF

terraform -chdir=./terraform/ init
terraform -chdir=./terraform/ apply -auto-approve

rm ./terraform/jupyter-main-worker.zip
rm ./model-function.zip

python3 ./lambda/migrations/lambda_function.py
