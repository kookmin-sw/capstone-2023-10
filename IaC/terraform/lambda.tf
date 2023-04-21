resource "aws_lambda_function" "main-worker" {
  function_name = "${var.prefix}-main-worker"
  filename = var.lambda_zip_file
  handler = "${var.lambda_handler_file}.lambda_handler"
  runtime = "python3.9"
  memory_size = 1 * 1024
  timeout = 120
  role = aws_iam_role.lambda-role.arn
}

resource "aws_iam_role" "lambda-role" {
  name = "${var.prefix}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      },
    ]
  })
}

# lambda policy
resource "aws_iam_role_policy_attachment" "lambda-attach-ssm-policy" {
  role = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "lambda-attach-ec2-full-access" {
  role = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-attach-ssm-full-access" {
  role = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}
