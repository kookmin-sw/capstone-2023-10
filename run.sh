#!/bin/bash

# Detect the operating system
OS=$(uname -s)

if [ "$OS" = "Darwin" ]; then
  # MacOS
  brew update
  brew install python@3.9
  brew install hashicorp/tap/terraform@1.4.5

elif [ "$OS" = "Linux" ]; then
  # Ubuntu or RedHat
  if [ -f "/etc/lsb-release" ]; then
    # Ubuntu
    sudo apt-get update
    sudo apt-get install python3.9
    sudo apt-get install -y wget unzip
    wget https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_linux_amd64.zip
    unzip terraform_1.4.5_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
  elif [ -f "/etc/redhat-release" ]; then
    # RedHat
    sudo yum update
    sudo yum install python39
    sudo yum install -y wget unzip
    wget https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_linux_amd64.zip
    unzip terraform_1.4.5_linux_amd64.zip
    sudo mv terraform /usr/local/bin/
  fi

elif [ "$OS" = "Windows_NT" ]; then
  # Windows
  $PYTHON_URL = "https://www.python.org/ftp/python/3.9.2/python-3.9.2-amd64.exe"
  $INSTALLER = "python-3.9.2-amd64.exe"
  $TEMP_DIR = "$($env:TEMP)\$($INSTALLER)"

  Invoke-WebRequest -Uri $PYTHON_URL -OutFile $TEMP_DIR

  & $TEMP_DIR /quiet InstallAllUsers=1 PrependPath=1

  Remove-Item $TEMP_DIR

  $TERRAFORM_URL = "https://releases.hashicorp.com/terraform/1.4.5/terraform_1.4.5_windows_amd64.zip"
  $ZIP_FILE = "terraform_1.4.5_windows_amd64.zip"
  $TEMP_DIR = "$($env:TEMP)\$($ZIP_FILE)"

  Invoke-WebRequest -Uri $TERRAFORM_URL -OutFile $TEMP_DIR

  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [System.IO.Compression.ZipFile]::ExtractToDirectory($TEMP_DIR, "$($env:TEMP)\terraform")

  Move-Item "$($env:TEMP)\terraform\terraform.exe" "C:\Windows\System32\terraform.exe"

  Remove-Item $TEMP_DIR
  Remove-Item -Recurse "$($env:TEMP)\terraform"

else
  echo "Unsupported operating system: $OS"
  exit 1
fi

terraform init
terraform apply

python3 ./lambda/lambda_function.py
