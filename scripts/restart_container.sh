sudo docker stop taxi_fare_prediction || true
sudo docker rm taxi_fare_prediction || true
sudo docker pull arist0craft/taxi_fare_prediction:latest
sudo docker run \
    -d \
    -p 8080:$PORT \
    --name taxi_fare_prediction \
    --restart always \
    --env SECRET_KEY=$SECRET_KEY \
    --env TG_BOT_TOKEN=$TG_BOT_TOKEN \
    --env TG_BOT_TOKEN=$TG_BOT_TOKEN \
    --env TG_WEBHOOK_URL=$TG_WEBHOOK_URL \
    --env GEOCODE_API_KEY=$GEOCODE_API_KEY \
    --env TG_WEBHOOK_CERTIFICATE="$TG_WEBHOOK_CERTIFICATE" \
    arist0craft/taxi_fare_prediction:latest
