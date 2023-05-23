resource "aws_security_group" "efs-sg" {
  vpc_id = aws_vpc.vpc.id
  name   = "${var.prefix}-efs-sg"
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
    from_port        = 2049
    protocol         = "tcp"
    to_port          = 2049
    description      = "sg"
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  }]
}

resource "aws_efs_file_system" "efs" {
  creation_token = "${var.prefix}-efs"
}

resource "aws_efs_mount_target" "efs-mount-target" {
  subnet_id       = aws_subnet.subnet.id
  file_system_id  = aws_efs_file_system.efs.id
  security_groups = [aws_security_group.efs-sg.id]
}
