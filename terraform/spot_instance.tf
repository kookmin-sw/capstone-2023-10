resource "aws_security_group" "spot-sg" {
  vpc_id = aws_vpc.vpc.id
  name = "${var.prefix}-spot-sg"
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
    from_port = 0
    protocol = "tcp"
    to_port = 0
    description      = "sg"
    ipv6_cidr_blocks = []
    prefix_list_ids  = []
    security_groups  = []
    self             = false
  } ]
}

resource "aws_iam_role" "spot-instance-role" {
  name = "${var.prefix}-spot-instance-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

# spot instance policy
resource "aws_iam_role_policy_attachment" "spot-attach-ssm-policy" {
  role = aws_iam_role.spot-instance-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "spot-attach-ssm-full-access" {
  role = aws_iam_role.spot-instance-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMFullAccess"
}

resource "aws_iam_role_policy_attachment" "spot-attach-EFS-client-full-access-policy" {
  role = aws_iam_role.spot-instance-role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonElasticFileSystemClientFullAccess"
}

resource "aws_iam_instance_profile" "spot-instance-role-profile" {
  role = aws_iam_role.spot-instance-role.name
  name = "${var.prefix}-spot-instance-role-profile"
}