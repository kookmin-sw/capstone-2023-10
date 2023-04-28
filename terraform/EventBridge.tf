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

resource "aws_cloudwatch_event_target" "spot_instance_interrupt_handler" {
  rule      = aws_cloudwatch_event_rule.spot_instance_interrupt_warning.name
  arn       = aws_lambda_function.main-worker.arn
  target_id = "${var.prefix}-spot-instance-interrupt-handler"
}
