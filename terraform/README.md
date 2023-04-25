## 테라폼 사용법

1. 먼저 테라폼을 설치한다. 
  ```
    # mac
    brew install terraform
  ```

2. IaC/terraform 디렉토리에서 다음 명령어를 입력한다.
  ```
    terraform init
  ```

3. 완료되고 다음 명령어를 실행하면 aws 인프라가 실행된다.
  ```
    terraform apply
  ```

4. "Enter a value:" 가 뜨면 yes를 입력한다.
   
5. 이후 실행된 aws 리소스들을 제거하려면 다음 명령어를 실행한다.
  ```
    terraform destroy
  ```

## 설정해줘야 하는 것들

1. aws config, credentials에 'kmubigdata'에 대한 정보가 있어야한다.
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
   * 해당 파일에서 region prefix instance_type key_name ami를 설정할 수 있다.
     * region : 리소스들이 생성될 리전을 입력한다. profile의 리전과 같도록 설정.
     * prefix : 생성될 리소스들의 이름 앞에 붙을 문자. 예를 들어 prefix가 "example"이면 생성된 VPC 이름은 "example-vpc"가 된다.
     * instance_type : 생성될 인스턴스의 타입 (t3.small)
     * key_name : 생성된 인스턴스에 사용할 키페어 이름
     * ami : 생성될 인스턴스의 ami
  
4. 각 tf 파일을 열어보면 각각의 리소스에서 설정 값들을 변경할 수 있다.

---

## How to Use Terraform

1. First, install Terraform.

