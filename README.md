# Django Docker Sample #

This sample project was built to demonstrate several principles:

  1. Running a Django project in Docker
  2. Use of Docker's "multi-stage" build process
  3. Use of `docker-compose` for development of the application
  4. Use of Celery in Docker for asynchronous tasks
  5. Uses advanced syntax for repeating sections of the `docker-compose.yml` file
  6. Uses nginx in the 'live' version of the `docker-compose.yml` for static files
  7. Describe the approach for user-provided media files

There is a lot to discover in this simple application.  It is meant for you to become familiar with 
the concepts and customize adapt them to your needs.

At the heart of things, this is a simply Django 'hello world' application.

You will need to have [Docker](https://docs.docker.com/get-docker/) and [docker-compose](https://docs.docker.com/compose/install/) installed.

It helps to be at least somewhat familiar with Docker and the syntax and details 
for the [Dockerfile](https://docs.docker.com/engine/reference/builder/) 
and [docker-compose.yml](https://docs.docker.com/compose/compose-file/) files.

The `Dockerfile` and `docker-compose.yml` files are well commented, but use the above references if more details are needed.


## Running the development application ##

In the directory containing this README file, simply run `docker-compose up` to build the initial images and start the containers. The
logs for each service will appear.  To end the services, press `Ctrl+C`

The command `docker-compose -d` will run the services in the background so you can use the terminal for other things. 
View the logs of the background processes with `docker-compose logs -f app tasks` (view the logs from the 'app' and 'tasks' services).
When running in background, use the command `docker-compose down` to stop all of the services.

Once started, point a browser to [http://localhost:8000](http://localhost:8000) to view the
results.

The development containers reference the application's `project` parent directory, so changes made to the 
application can be easily viewed without needing to rebuild anything, but a restart may be needed.
Note that the 'app' service is running `manage.py runserver`, so it will restart as changes are
made to the application code.  The 'task' container will need to be restarted to pick up the
code changes.

While it shouldn't normally be needed, you can force a rebuild of the images (using
fresh copies of the parent 'FROM' images) with the commands:

    docker-compose build --pull 
    docker-compose pull

The last command will pull fresh copies of the static images (`postgres` and `redis`).

These commands can also be invoked from the `./build-dev.sh` script.

## Running the 'live' application ##

Once you have made any changes and tested them in the development environment, you would normally want to build
formal Docker images in a CI/CD pipeline or workflow, then reference those in your production
environment.  One advantage is that the production images will look very similar to your
desktop development.  Since the Dockerfile includes all of the application dependencies into the image, there
is little configuration on the production machine.

### Building the Docker images ###

This will require static Docker images to be built.  In the directory with the README file, invoke the two commands.
**NOTE** the period at the end of each line!

    docker build --target applayer --tag my_app_image .
    docker build --target staticlayer --tag my_static_image .

For simplicity, you can also run `./build-live.sh`

You can use these images locally, but if you wanted to push them to a registry you will need to use appropriate tag 
names.  For Docker Hub, you will need your username followed by a slash followed by the image name.  If you use another
registry, you would preface it with the domain name.  Such a full name might look like 
`my.registry.com/username/imagename`  Once the image has been tagged appropriately, you can use `docker push` followed 
by the full image name.  The build and push process could be done by a CI/CD process, but that is more than
we need for this demonstration and custom to your configuration.

### Starting the 'live' copy of the services ###

From the directory with the README file, type `cd live`,  This directory holds just the
files we need to run our simulated production application.

The configuration for the nginx server can be found in the `httpd/default.conf` file,
which gets pulled into the staticlayer image with the rest of the static files.

The `docker-compose.yml` file in this directory references our built images and
also a real nginx process in the 'httpd' service.  This is the entry point for our application and will handle the static files for us, and also pass Django requests to the 'app' service.

Start the 'live' environment with `docker-compose up -d`.

Once everything has started, visit [http://localhost:8001](http://localhost:8001) to view the results.  Note that
the 'debug' setting has been turned off.  

You shouldn't see other changes from our development version of the application, however the static image is no longer coming from Django, but from the nginx web server.

## Handling of media files ##

Support for User-uploaded files, like profile pictures, can be added to the application [normally](https://docs.djangoproject.com/en/3.2/topics/files/).

There are comments in the `httpd/default.conf` and the `live/docker-compose.yml` files to
indicate what would be needed.

The only requirement is storing them on a device that can be accessed by the `app` container and the `httpd` (nginx)
container.  For this example, a local directory will be used.  The `live/docker-compose.yml` can be modified to indicate this volume:

    app:
      ...
      volumes:
        - /my/media/:/code/media
    httpd:
      ...
      volumes:
        - /my/media/:/code/media:ro

Notice the `:ro` suffix on the volume in the `httpd` container, which limits that container to read-only access. 
This prevents anyone who might hack into the container from messing with our files.  In fact, since the static files are
built into the image, should our website somehow get defaced, all we have to do is restart the
container and everything will be reset to the original pristine condition.

Certainly, if the `tasks` or `cmd` containers need access to the media files, the volume could be added to their
respective sections, with or without the read-only suffix as appropriate.

Other than the changes to the Django settings and application, the file `httpd/default.conf` will need to have
the section for media uncommented before building the Docker images.


## Making this your own ##

You can make changes in the development environment: Try changing the web page found in the `projects/hello/templates/hello_world.html` file.  Check this in the development 
url (port 8000) and verify that the changes don't appear in the 'live' url (port 8001) until the images are rebuilt and the services restarted.

Many other configuration entries might be included in the environment files or in other, more secure, secrets files.

It is quite possible to include a more secure configuration for Nginx, and even reference SSL certificates and private 
key files, although you should reference such sensitive files as docker-compose 'volumes' rather than build them into the images.

