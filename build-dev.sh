#!/bin/bash
# Build the images for the development environment as defined in the docker-compose.yml file
docker-compose build --pull

# Refresh other images used by our services (postgres, redis) in the docker-compose.yml file
docker-compose pull
