#!/bin/bash
# Build the Docker images for use in the 'live' environment

docker build --target applayer --tag my_app_image .
docker build --target staticlayer --tag my_static_image .

#
echo "Build complete! Now do the following:"
echo "  cd live"
echo "  docker-compose up -d"
echo "This will start the services and listen on http://localhost:8001"
