resource "aws_cloudwatch_event_rule" "spot_instance_interrupt_warning" {
  name        = "spot-instance-interrupt-warning"
  description = "Spot instance interrupt warning"

  event_pattern = <<PATTERN
{
  "source": ["aws.ec2"],
  "detail-type": ["EC2 Spot Instance Interruption Warning"]
}
PATTERN
}

resource "aws_cloudwatch_event_rule" "start_of_every_hour" {
  name                = "start_of_every_hour"
  description         = "Fires at the start of every hour"
  schedule_expression = "cron(0 * * * ? *)"
}

resource "aws_cloudwatch_event_target" "spot_instance_interrupt_handler" {
  rule      = aws_cloudwatch_event_rule.spot_instance_interrupt_warning.name
  arn       = aws_lambda_function.main-worker.arn
  target_id = "${var.prefix}-spot-instance-interrupt-handler"
}

resource "aws_cloudwatch_event_target" "start_of_every_hour_handler" {
  rule      = aws_cloudwatch_event_rule.start_of_every_hour.name
  arn       = aws_lambda_function.model-function.arn
  target_id = "${var.prefix}-start_of_every_hour_handler"
}
