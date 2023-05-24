resource "aws_ssm_parameter" "iam_role_parameter" {
  name  = "IAM_ROLE_ARN"
  type  = "String"
  value = aws_iam_instance_profile.spot-instance-role-profile.arn
}

resource "aws_ssm_parameter" "efs_parameter" {
  name  = "EFS_ID"
  type  = "String"
  value = aws_efs_file_system.efs.id
}

resource "aws_ssm_parameter" "subnet_parameter" {
  name  = "SUBNET_ID_${var.region}a"
  type  = "String"
  value = aws_subnet.subnet.id
}

resource "aws_ssm_parameter" "subnet2_parameter" {
  name  = "SUBNET_ID_${var.region}b"
  type  = "String"
  value = aws_subnet.subnet2.id
}

# resource "aws_ssm_parameter" "subnet3_parameter" {
#   name  = "SUBNET_ID_${var.region}c"
#   type  = "String"
#   value = aws_subnet.subnet3.id
# }

resource "aws_ssm_parameter" "sg_parameter" {
  name  = "SECURITYGROUP_ID"
  type  = "String"
  value = aws_security_group.spot-sg.id
}

resource "aws_ssm_parameter" "lb_parameter" {
  name  = "LOAD_BALANCER_NAME"
  type  = "String"
  value = aws_lb.alb.name
}

resource "aws_ssm_parameter" "lb_tg_parameter" {
    name = "TARGET_GROUP_ARN"
    type = "String"
    value = aws_lb_target_group.lb-tg.arn
}

resource "aws_ssm_parameter" "lmabda_url" {
    name = "LAMBDA_FUNCTION_URL"
    type = "String"
    value = aws_lambda_function_url.main-worker-url.function_url
}

resource "aws_ssm_parameter" "model_url" {
    name = "MODEL_FUNCTION_URL"
    type = "String"
    value = aws_lambda_function_url.model-function-url.function_url
}
