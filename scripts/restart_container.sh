sudo docker stop taxi_fare_prediction || true
sudo docker rm taxi_fare_prediction || true
sudo docker pull arist0craft/taxi_fare_prediction:latest
sudo docker run \
    -d \
    -p 8080:$PORT \
    --name taxi_fare_prediction \
    --restart always \
    arist0craft/taxi_fare_prediction:latest
