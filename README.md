# ndlib-rest
Network Diffusion Library REST Service.

This project offers a REST interface for the [ndlib](https://github.com/GiulioRossetti/ndlib) Python library.


#### Tools
* REST service: ndrest.py
  * Web API docs: http://127.0.0.1:5000/docs
  * Unittest: ndlib-rest/service_test
* ndlib: ndlib-rest/ndlib
  * Unittest: ndlib-rest/ndlib/ndlib_test
* Python REST client: ndlib-rest/client


Python 2.7 required dependencies:

- abc
- flask 
- flask-cors
- flask_restful
- flask_apidoc
- networkx
- numpy
- shelve

#### REST service setup
Local testing
```python
    python ndrest.py
```

Local testig with multiple workers (using [gunicorn](http://gunicorn.org/) web server):
```bash
    gunicorn -w num_workers -b 127.0.0.1:5000 ndrest:app
```

In order to change the binding IP/port modify the apidoc.json file.
To update the API page run the command:
```
    apidoc -i ndlib-rest/ -o ndlib-rest/static/docs
```


#### Docker Container
The web application is shipped in a [Docker](https://www.docker.com/) container.
You can use the Dockerfile to create a new image and run the web application using the gunicorn application server.

To create the Docker image, install Docker on your machine.
To create the image execute the following command from the local copy of the repository

```
docker build -t [tagname_for_your_image] .
```
The command create a new image with the specified name. Pay attention to the ```.``` a the end of the command.

```
docker run -d -i -p 5000:5000 [tagname_for_your_image] 
```
This command execute a container with the previous image, boungin the local port 5000 to the internal port of the container. 
The option ```-d``` make the container to run in the background (detached)

To have a list of all active container
```
docker ps -al
```

To stop a container 

```
docker stop container_name
```
