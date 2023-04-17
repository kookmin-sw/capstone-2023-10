resource "aws_security_group" "ec2-sg" {
  vpc_id = aws_vpc.vpc.id
  name = "${var.prefix}-ec2-sg"
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

resource "aws_instance" "main-worker" {
  ami = var.ami
  subnet_id = aws_subnet.subnet.id
  security_groups = [ aws_security_group.ec2-sg.id ]
  instance_type = var.instance_type
  key_name = var.key_name
  iam_instance_profile = aws_iam_instance_profile.ec2role-instance-profile.name
  tags = {
    "Name" = "${var.prefix}-main-worker"
  }
  user_data = <<-EOF
    #!/bin/bash
    sudo apt update -y
    sudo apt install -y nginx
    EOF
}

resource "aws_iam_role" "ec2role" {
  name = "${var.prefix}-e2c-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Sid    = ""
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2role-attach-ssm-policy" {
  role = aws_iam_role.ec2role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "ec2role-attach-ec2-full-access" {
  role = aws_iam_role.ec2role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2FullAccess"
}

resource "aws_iam_role_policy_attachment" "ec2role-attach-s3-full-access" {
  role = aws_iam_role.ec2role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonS3FullAccess"
}

resource "aws_iam_role_policy_attachment" "ec2role-attach-route53-full-access" {
  role = aws_iam_role.ec2role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRoute53FullAccess"
}

resource "aws_iam_role_policy_attachment" "ec2role-attach-EFS-client-full-access-policy" {
  role = aws_iam_role.ec2role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonElasticFileSystemClientFullAccess"
}

resource "aws_iam_instance_profile" "ec2role-instance-profile" {
  name = "${var.prefix}-ec2-role-instnace-profile"
  role = aws_iam_role.ec2role.name
}

