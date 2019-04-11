FROM python:3.6 as appbuilder

ARG USERNAME=user1
ARG USERUID=1000
ARG USERGID=1000

ENV PYTHONUNBUFFERED 1

ADD wait_entrypoint.py /
ADD ./requirements.txt /
RUN pip install --no-cache-dir -r /requirements.txt

# Add in a user (change as needed for a non-root user)
RUN addgroup --gid 1000 user1000 \
        && adduser --firstuid $USERUID  --gid $USERGID \
		--gecos "$USERNAME" \
		--disabled-password $USERNAME \
        && mkdir /code

# If we have other Debian packages to install...
# RUN apt-get update && apt-get install -y \
#                 graphviz \
#         && apt-get clean \
#         && rm -fr /var/lib/apt/lists/*

WORKDIR /code

ADD ./project /code

RUN python -m compileall -q -x '/\.git' . \
	&& echo "Application filesystem configured"

#------------
FROM appbuilder as applayer

ARG USERNAME=user1

USER $USERNAME

#------------
FROM appbuilder as staticbuilder

RUN export SECRET_KEY=x \
	&& python manage.py collectstatic --no-input -v0 \
	&& echo "Static filesystem populated"

#------------
FROM nginx:latest as staticlayer

EXPOSE 80

VOLUME /var/log/nginx

COPY --from=staticbuilder /code/static/ /code/static/
COPY httpd/ /code/httpd/

RUN cp /code/httpd/nginx.conf /etc/nginx/conf.d/default.conf
