resource "aws_lambda_function" "main-worker" {
  function_name = "${var.prefix}-main-worker"
  filename      = "jupyter-main-worker.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  memory_size   = 1 * 1024
  timeout       = 900
  role          = aws_iam_role.lambda-role.arn
}

resource "aws_lambda_function" "model-function" {
  function_name = "${var.prefix}-model-function"
  filename      = "model-function.zip"
  handler       = "lambda_function.lambda_handler"
  runtime       = "python3.9"
  memory_size   = 1 * 1024
  timeout       = 900
  role          = aws_iam_role.lambda-role.arn
}

resource "aws_lambda_function_url" "main-worker-url" {
  function_name = aws_lambda_function.main-worker.function_name
  authorization_type = "NONE"
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
  role       = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "lambda-attach-ec2-full-access" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-attach-S3-full-access" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-attach-ssm-full-access" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}

resource "aws_iam_role_policy_attachment" "lambda-attach-spot-fleet-tagging-role" {
  role       = aws_iam_role.lambda-role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonEC2SpotFleetTaggingRole"
}
