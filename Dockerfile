# Defining arguments before the first FROM makes it global to all stages of the 
# entire Dockerfile

ARG USERNAME=user1

#------------ Stage 1: The appbuilder stage with software and user
FROM python:3.9 as appbuilder

ARG USERNAME
ARG USERUID=1000
ARG USERGID=1000

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1

ADD wait_entrypoint.py /
ADD ./requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# Create our non-root user
RUN addgroup --gid $USERGID $USERNAME \
        && adduser --firstuid $USERUID  --gid $USERGID \
		--gecos "$USERNAME" \
		--disabled-password $USERNAME

# If we have other Debian packages to install...
# RUN apt-get update && apt-get install -y \
#                 graphviz \
#         && apt-get clean \
#         && rm -fr /var/lib/apt/lists/*


# Create /code and copy the django project to it
ADD project/ /code

WORKDIR /code

ENV PATH="/code:${PATH}"

RUN python -m compileall -q -x '/\.git' . \
	&& echo "Application filesystem configured"
#----- End of Stage 1: At this point we have a good base layer with our app and dependencies

#------------ Stage 2: We want to extend the base layer from Stage 1 by bycoming our non-root user
FROM appbuilder as applayer

ARG USERNAME

USER $USERNAME
#------ End of Stage 2: We can safely run this layer, as it is not root

#------------ Stage 3: Build the static content
FROM appbuilder as staticbuilder


RUN export SECRET_KEY=x \
	&& python manage.py collectstatic --no-input -v0 \
	&& echo "Static filesystem populated"

#------ End of Stage 3: We have our application and static content in a layer we need temporarily

#------------ Stage 4: Build our nginx web server with just the static content (no other application layer files)
FROM nginx:latest as staticlayer

EXPOSE 80

# Define logs so they can be persisted between restarts if desirable
VOLUME /var/log/nginx

## todo: place at default and fix config
# Pull in only the static files from the earlier stage
COPY --from=staticbuilder /code/static/ /code/static/

# Pull in any extra web server configurations
COPY httpd/ /etc/nginx/conf.d/

#------ End of Stage 4: Just a web server, our static content and a configuration file
