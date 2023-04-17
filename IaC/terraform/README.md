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


## 설정 변경을 원할 시
1. variables.tf의 값을 변경하면 해당값이 적용된다.

2. 각 tf 파일의 내용을 변경한다.