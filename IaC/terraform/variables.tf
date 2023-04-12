variable "region" {
  type = string
  default = "ap-northeast-2"
}

variable "prefix" {
  type = string
  default = "sh-capstone"
}

variable "instance_type" {
  type = string
  default = "t3.small"
}

variable "key_name" {
  type = string
  default = "ksh-seoul"
}

variable "ami" {
  type = string
  default = "ami-04cebc8d6c4f297a3" 
}