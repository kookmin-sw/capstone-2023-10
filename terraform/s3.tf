resource "aws_s3_bucket" "jupyter-log-s3" {
    bucket = "${var.prefix}-system-log"

    force_destroy = true
}