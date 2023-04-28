resource "aws_security_group" "alb-sg" {
  vpc_id = aws_vpc.vpc.id
  name   = "${var.prefix}-alb-sg"
  egress = [{
    cidr_blocks      = ["0.0.0.0/0"]
    from_port        = 0
    protocol         = -1
    to_port          = 0
    description      = "sg"
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  }]
  ingress = [{
    cidr_blocks      = ["0.0.0.0/0"]
    from_port        = 80
    protocol         = "tcp"
    to_port          = 80
    description      = "sg"
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
    },
    {
      cidr_blocks      = ["0.0.0.0/0"]
      from_port        = 8800
      protocol         = "tcp"
      to_port          = 8800
      description      = "sg"
      ipv6_cidr_blocks = []
      prefix_list_ids  = []
      security_groups  = []
      self             = false
  }]
}

resource "aws_lb" "alb" {
  subnets                    = [aws_subnet.subnet.id, aws_subnet.subnet2.id]
  internal                   = false
  name                       = "${var.prefix}-alb"
  enable_deletion_protection = false
  security_groups            = [aws_security_group.alb-sg.id]
  load_balancer_type         = "application"
}

resource "aws_lb_target_group" "lb-tg" {
  name     = "${var.prefix}-tg"
  port     = 80
  protocol = "HTTP"
  vpc_id   = aws_vpc.vpc.id
}

resource "aws_lb_listener" "lb-listener" {
  load_balancer_arn = aws_lb.alb.arn
  port              = "80"
  protocol          = "HTTP"
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.lb-tg.arn
  }
}
