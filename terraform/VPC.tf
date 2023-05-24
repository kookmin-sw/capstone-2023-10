resource "aws_vpc" "vpc" {
  cidr_block           = "10.7.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    "Name" = "${var.prefix}-vpc"
  }
}

resource "aws_subnet" "subnet" {
  vpc_id                                      = aws_vpc.vpc.id
  cidr_block                                  = "10.7.0.0/24"
  availability_zone                           = "${var.region}a"
  enable_resource_name_dns_a_record_on_launch = true
  map_public_ip_on_launch                     = true
  tags = {
    "Name" = "${var.prefix}-subnet"
  }
}

resource "aws_subnet" "subnet2" {
  vpc_id                                      = aws_vpc.vpc.id
  cidr_block                                  = "10.7.1.0/24"
  availability_zone                           = "${var.region}b"
  enable_resource_name_dns_a_record_on_launch = true
  map_public_ip_on_launch                     = true
  tags = {
    "Name" = "${var.prefix}-subnet2"
  }
}

# resource "aws_subnet" "subnet3" {
#   vpc_id                                      = aws_vpc.vpc.id
#   cidr_block                                  = "10.7.2.0/24"
#   availability_zone                           = "${var.region}c"
#   enable_resource_name_dns_a_record_on_launch = true
#   map_public_ip_on_launch                     = true
#   tags = {
#     "Name" = "${var.prefix}-subnet3"
#   }
# }

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.vpc.id
  tags = {
    "Name" = "${var.prefix}-igw"
  }
}

resource "aws_route_table" "rt" {
  vpc_id = aws_vpc.vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }
  tags = {
    "Name" = "${var.prefix}-rt"
  }
}

resource "aws_route_table_association" "rta" {
  route_table_id = aws_route_table.rt.id
  subnet_id      = aws_subnet.subnet.id
}

resource "aws_route_table_association" "rta2" {
  route_table_id = aws_route_table.rt.id
  subnet_id      = aws_subnet.subnet2.id
}

# resource "aws_route_table_association" "rta3" {
#   route_table_id = aws_route_table.rt.id
#   subnet_id      = aws_subnet.subnet3.id
# }
