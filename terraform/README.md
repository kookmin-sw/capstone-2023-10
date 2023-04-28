## 테라폼 사용법

1. 먼저 테라폼을 설치한다. 
  ```
  # mac
  brew install terraform
  ```

2. terraform 파일(.tf)이 있는 디렉토리에서 다음 명령어를 입력한다.
  ```
  terraform init
  ```

3. 완료되고 다음 명령어를 실행하면 인프라 구축이 시작된다.
  ```
  terraform apply
  ```

4. "Enter a value:" 가 뜨면 yes를 입력한다.
   
5. 생성된 클라우드 리소스들을 제거하려면 다음 명령어를 실행한다.
  ```
  terraform destroy
  ```

## 설정해줘야 하는 것들

1. aws config, credentials에 클라우드 벤더에 대한 정보가 있어야한다.
  * 예시
    ```
    # config
    [default]
    region = ap-northeast-2
    ```

    ```
    # credentials
    [default]
    aws_access_key_id = **********
    aws_secret_access_key = ****************************
    ```

2. main.tf의 profile에 해당 profile 이름을 넣는다.
   * 위의 예시로는 default.
   * 만약 위의 []안이 default가 아니라면 해당값을 넣는다.

3. variables.tf의 값들을 변경한다.
   * 해당 파일에서 region, prefix를 설정할 수 있다.
     * region : 리소스들이 생성될 리전을 입력한다. profile의 리전과 같도록 설정.
     * prefix : 생성될 리소스들의 이름 앞에 붙을 문자열. 예를 들어 prefix가 "example"이면 생성된 VPC 이름은 "example-vpc"가 된다.
  
4. 각 리소스 tf 파일에서 리소스들의 설정 값들을 변경할 수 있다.

---

## How to Use Terraform

1. First, install Terraform.
  ```
  # mac
  brew install terraform
  ```

2. Go to the directory where the Terraform file (.tf) is located and run the following command.
  ```
  terraform init
  ```

3. After completion, run the following command to start building the infrastructure.
  ```
  terraform apply
  ```

4. When "Enter a value:" appears, enter "yes".

5. To remove the created cloud resources, run the following command.
  ```
  terraform destroy
  ```

## Required Configurations
1. The AWS config and credentials must contain information about the cloud vendor.
  * Example:
    ``` 
    # config
    [default]
    region = ap-northeast-2
    ```

    ```
    # credentials
    [default]
    aws_access_key_id = **********
    aws_secret_access_key = ****************************
    ```

2. In the main.tf file, enter the profile name in the profile section.
  * For example, it is "default" based on the above example.
  * If the value in the [] is not "default", enter the corresponding value.

3. Change the values in the variables.tf file.
  * In this file, you can set the region and prefix.
    * region: Enter the region where the resources will be created. Set it to the same region as the profile.
    * prefix: A string that will be added to the beginning of the names of the created resources. For example, if the prefix is "example", the name of the created VPC will be "example-vpc".

4. In each resource tf file, you can change the configuration values of the resources.
