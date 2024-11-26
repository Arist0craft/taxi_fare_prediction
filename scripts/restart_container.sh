docker stop taxi_fare_prediction || true
docker pull arist0craft/taxi_fare_prediction:latest
docker run \
    -d \
    -p 8080:$PORT \
    --rm \
    --name taxi_fare_prediction \
    --restart always \
    arist0craft/taxi_fare_prediction:latest
