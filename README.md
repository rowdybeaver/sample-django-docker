# Django Docker Sample

This was built in reference 
to [a question on Reddit's Django forum](https://old.reddit.com/r/django/comments/bboibg/best_way_to_deploy_a_django_application_ansible/), 
however this question has been asked before and a working set of examples was needed.


This project provides an example for a Django application running under
Docker and docker-compose.  It is meant for you to become familiar with the concepts and customize to your needs.


This is not meant to be a fully functional application.  Indeed, it is almost completely from a 
regular ```django-admin startproject project```, with changes made to settings.py to support some
sample environment settings.

This is meant to show the general structure of Django and Docker components.


A very minimal sample Django project is included for testing and demonstration, with the imaginative name ```project```.


It helps to be at least somewhat familiar with Docker and the syntax and details 
for the [Dockerfile](https://docs.docker.com/engine/reference/builder/) 
and [docker-compose.yml](https://docs.docker.com/compose/compose-file/) files.


## The ```Dockerfile```

Normally, the Dockerfile has a single 'FROM' base image and results in a single image, a **target**.  With a 
multi-stage Dockerfile, there are several targets, allowing all (or some) of a previous target 
can be referenced.

This process assumes you have a Django project in the current directory (I use the name 'project' in the Dockerfile). We will
also use a non-root user when running our application, so we will configure that, too.  It is a good security practice.

The Dockerfile in this repo has several targets:

    - 'appbuilder' - build on the python:3.6 and add Django, our application and its particular requirements, also creates a non-root user (a security precaution)
    - 'applayer' - this target simply changes the default user (so it isn't 'root')
    - 'staticbuilder' - build on the appbuilder layer to collect static files
    - 'staticlayer' - references the NGINX and adds in configuration and just the static files

We will only deploy two of these targets:

    - applayer  Used for our compiled project files and for execution (runserver/uwsgi/gunicorn and celery)
  
    - staticlayer  Our dockerized web server and reverse proxy
    
    
## The ```docker-compose.yml``` file

The docker-compose.yml file will start the following containers:

    - db  - The public postgres image
    - redis - The public redis image
    - app - The 'applayer' target running (runserver/uwsgi/gunicorn)
    - tasks - The 'applayer' target running celery task 
    - httpd - The 'staticlayer' target as our web server
    
Because Docker might start the 'app' container before the 'db' is ready, there is a ```wait_entrypoint.py``` script, to 
ensure resources are accepting network connections.  Once the connections are opened, the compose file's ```command``` 
will be invoked.


## Development Environment

The enclosed ```docker-compose.yml``` file will build the necessary target images, with some default image names (we
don't even need to know the image names).


### Building the development images

We can test our ```Dockerfile``` build process by running:
     
     docker-compose build --pull

While the example project is simply a raw install of Django with a Postgres database.  The only other changes were to 
show how the ```SECRET_KEY``` and ```POSTGRES_PASSWORD``` could be provided via environment variables (in 
the ```unittest.env```).  The ```project/settings.py``` file also has several changes, including database, Celery, 
and a ```STATIC_ROOT``` setting.

For our testing, the ```app```definition will launch the application the ```runserver```.

Although referenced in the ```tasks``` definition in the ```docker-compose.yml``` file, the sample application code 
does not have any Celery tasks defined (and there is no ```celery.py``` definition).  It is there as an example, to
demonstrate that the same target can be built and referenced for different purposes.

The ```httpd``` task only forces a build of the ```staticlayer``` target, but does nothing (```/bin/true``` returns 
exit code zero).  We don't need a web server in development, but we **do** want to ensure it can be built.


### Launching the containers

To launch the application, run the command:

    docker-compose up

Visiting [http://localhost:8000]() will let you know if Django is running.    

Since the project directory is made directly available in the ```app``` container (with the ```volumes``` directive), 
it will be restarted as changes are made.  This is precisely what we want in a development environment, but not 
good for a live deployment.

Note that the ```tasks``` service will exit immediately (there is nothing in our code for it), but even in
development, this service would need to be restarted in order to pick up code changes.


The development environment can be shut down with the command:

    docker-compose down
    
Note that this **does** keep our database, since we placed it on a named volume.  Next time we bring the environment up,
the data would be available to us.  The volume can be removed completely with ```docker-compose down --volumes```


## CI/CD: Getting to a Live Deployment

In development, we referenced the targets from the ```Dockerfile``` directly, and they are built when requested with
the ```docker-compose build --pull``` command.

For a live deployment, we want to name our Docker images.  In the process of deploying your application through some
CI/CD pipeline, the images can be built with the commands:

    docker build --target applayer --tag my-applayer:latest .
    docker build --target staticlayer --tag my-staticlayer:latest .
    
These commands create images that can be pushed to a Docker Registry.  They can have version tags.  It is strongly 
suggested to use specifically named versions instead of ```latest```, since it is the default.  That way you can roll 
back to a prior version of your image.


## The Live deployment

The ```live-docker-compose.yml``` file is very similar to the one we use for development, with notable exceptions:

  - The database volume has been renamed to ```live-db``` avoid conflict with development
  - The ```prod.env``` file is used for environment settings
  - The image names are referenced, rather than being built on demand
  - The ```app``` service runs the ```uwsgi``` command (```gunicorn``` can also be used as an alternative)
  - The ```httpd``` service connects to the ```app``` service

If demonstrating this on the same machine we used for development, be sure to shut down the development environment.

The command to bring up the environment is almost the same:

    docker-compose up -f live-docker-compose.yml
 
The test deployment should be accessible on [http://localhost:8001]()


## Making this your own

The ```DEBUG=True``` is still set: this is not desirable for a live environment, but needed for this demonstration.

Many other configuration entries might be included in the environment files or in other, more secure, secrets files.

It is quite possible to include a more secure configuration for Nginx, and even reference SSL certificates and private 
key files, although it is not recommended that these get built into the image files.

