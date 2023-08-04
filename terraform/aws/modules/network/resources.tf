
data "aws_availability_zones" "available" {}

locals {
  cluster_name = "cluster_${var.general.key_name}_${var.general.attack_range_name}"
}

module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"

  name                 = "vpc_${var.general.key_name}_${var.general.attack_range_name}"
  cidr                 = "10.0.0.0/16"
  azs                  = data.aws_availability_zones.available.names
  public_subnets       = ["10.0.1.0/24"]
  enable_dns_hostnames = true

}


resource "aws_security_group" "default" {
  name   = "sg_public_subnets_${var.general.key_name}_${var.general.attack_range_name}"
  vpc_id = module.vpc.vpc_id
}

resource "aws_security_group_rule" "all_vpc" {
  from_port   = -1
  to_port     = -1
  protocol    = "-1"
  cidr_blocks = ["10.0.0.0/16"]
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "icmp_wl" {
  from_port   = -1
  to_port     = -1
  protocol    = "icmp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "icmp" {
  from_port   = -1
  to_port     = -1
  protocol    = "icmp"
  cidr_blocks = ["10.0.0.0/16"]
  security_group_id = aws_security_group.default.id
  type = "ingress"
}


resource "aws_security_group_rule" "port_22" {
  from_port   = 22
  to_port     = 22
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_8000" {
  from_port   = 8000
  to_port     = 8000
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_8080" {
  from_port   = 8080
  to_port     = 8080
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}


resource "aws_security_group_rule" "port_8443" {
  from_port   = 8443
  to_port     = 8443
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}


resource "aws_security_group_rule" "port_9997" {
  from_port   = 9997
  to_port     = 9997
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_8089" {
  from_port   = 8089
  to_port     = 8089
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}
resource "aws_security_group_rule" "port_5986" {
  from_port   = 5986
  to_port     = 5986
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}


resource "aws_security_group_rule" "port_5985" {
  from_port   = 5985
  to_port     = 5985
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}
resource "aws_security_group_rule" "port_3389_t" {
  from_port   = 3389
  to_port     = 3389
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_3389" {
  from_port   = 3389
  to_port     = 3389
  protocol    = "udp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_8888" {
  from_port   = 8888
  to_port     = 8888
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_443" {
  from_port   = 443
  to_port     = 443
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_3391" {
  from_port   = 3391
  to_port     = 3391
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_2323" {
  from_port   = 2323
  to_port     = 2323
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_7999" {
  from_port   = 7999
  to_port     = 7999
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}


resource "aws_security_group_rule" "port_50051" {
  from_port   = 50051
  to_port     = 50051
  protocol    = "tcp"
  cidr_blocks = split(",", var.general.ip_whitelist)
  security_group_id = aws_security_group.default.id
  type = "ingress"
}

resource "aws_security_group_rule" "port_80" {
  from_port         = 80
  protocol          = "tcp"
  security_group_id = aws_security_group.default.id
  to_port           = 80
  type              = "ingress"
  cidr_blocks = split(",", var.general.ip_whitelist)
}

resource "aws_security_group_rule" "allow_all_outbound" {
  description       = "Allow all outbound traffic by default"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.default.id
  type              = "egress"
  cidr_blocks       = ["0.0.0.0/0"]
}