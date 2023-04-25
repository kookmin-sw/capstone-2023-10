resource "aws_security_group" "alb-sg" {
  vpc_id = aws_vpc.vpc.id
  name = "${var.prefix}-alb-sg"
  egress = [ {
    cidr_blocks = [ "0.0.0.0/0" ]
    from_port = 0
    protocol = -1
    to_port = 0
    description      = "sg"
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  } ]
  ingress = [ {
    cidr_blocks = [ "0.0.0.0/0" ]
    from_port = 80
    protocol = "tcp"
    to_port = 80
    description      = "sg"
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  } ]
}

resource "aws_lb" "alb" {
  subnets = [ aws_subnet.subnet.id, aws_subnet.subnet2.id ]
  internal = false
  name = "${var.prefix}-alb"
  enable_deletion_protection = false
  security_groups = [ aws_security_group.alb-sg.id ]
  load_balancer_type = "application"
}

resource "aws_lb_target_group" "main-worker-tg" {
  name     = "main-worker-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.vpc.id
}

# resource "aws_lb_target_group_attachment" "main-worker-tg-attachment" {
#   target_group_arn = aws_lb_target_group.main-worker-tg.arn
#   target_id = aws_lambda_function.main-worker.id
#   port = 80
# }

resource "aws_lb_target_group" "jupyter-tg" {
  name     = "jupyter-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.vpc.id
}

resource "aws_lb_listener" "main-worker-listener" {
  load_balancer_arn = aws_lb.alb.arn
  port = "80"
  protocol = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.main-worker-tg.arn
  }
}

resource "aws_lb_listener_rule" "jupyter-listener-rule" {
  listener_arn = aws_lb_listener.main-worker-listener.arn
  priority     = 100

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.jupyter-tg.arn
  }

  condition {
    path_pattern {
      values = ["/jupyter"]
    }
  }
}