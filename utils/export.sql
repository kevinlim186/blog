docker run -it --rm \
  yandex/clickhouse-client \
  --host 192.168.178.103 \
  --port 9000 \
  --user budol \
  --password=$CLICKHOUSEPASSWORD \
  --verbose \
  --query="" \ 
  > /Users/KevinLim/Downloads/your_output.csv