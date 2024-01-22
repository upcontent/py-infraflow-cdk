from aws_cdk.aws_ec2 import Port, Protocol

postgres_port = Port.tcp(5432)
mysql_port = Port.tcp(3306)
redis_port = Port.tcp(6379)
https_port = Port.tcp(443)
http_port = Port.tcp(80)
http_alt_port = Port.tcp(8080)
all_tcp = Port.all_tcp()