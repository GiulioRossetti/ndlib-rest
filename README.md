# NDlib-Rest - Network Diffusion Library REST Service.
[![Build Status](https://travis-ci.org/GiulioRossetti/ndlib-rest.svg?branch=master)](https://travis-ci.org/GiulioRossetti/ndlib-rest)

This project offers a REST interface for the [ndlib](https://github.com/GiulioRossetti/ndlib) Python library.


#### Tools
* REST service: ndrest.py
  * Web API docs: http://127.0.0.1:5000/docs
  * Unittest: ndlib-rest/service_test
* Python REST client: ndlib-rest/client


Python 3.6 required dependencies:

- [ndlib](https://github.com/GiulioRossetti/ndlib)==4.0.2
- flask==0.12
- flask-cors==3.0.2
- flask_restful==0.3.5
- flask_apidoc==1.0.0
- networkx==1.11
- numpy==1.12.0
- scipy==0.18.1
- [dynetx](https://github.com/GiulioRossetti/dynetx)==0.1.6

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
The web application (REST service and Viz framework) is shipped as a [Docker](https://www.docker.com/) container.
You can use the Dockerfile to create a new image and run the web application using the gunicorn application server.

To create the Docker image, install Docker on your machine.
To create the image execute the following command from the local copy of the repository

```
docker build -t [tagname_for_your_image] .
```
The command create a new image with the specified name. Pay attention to the ```.``` a the end of the command.

```
docker run -d -i -p 5000:5000 -p 8080:8080 [tagname_for_your_image] 
```
This command execute a container with the previous image, bind the local port 5000 to the internal port of the container. 
The option ```-d``` make the container to run in the background (detached)

To have a list of all active container
```
docker ps -al
```

To stop a container 

```
docker stop container_name
```
 ##### Prebuilt Docker image
 
To avoid docker image building just download the full container (beta version)
 
```
docker pull rossetti/ndrest:ndrest_beta
```
 
Once the image is ready run it as:

```
docker run -d -i -p 5000:5000 -p 8080:8080 rossetti/ndrest:ndrest_beta
```

## REST service details
In ndrest.py are specified limits for graph sizes. 
In particular it describes the minimum and maximum numbers of nodes (for both generators and loaded networks) as well as the maximum file sizes for upload.

```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB limit for uploads
max_number_of_nodes = 100000
min_number_of_nodes = 200 # inherited by networkx
```

- The "complete graph generator" endpoint represents the only exception to the specified lower bound on number of nodes: such model lowers the minimum to 100 nodes. Indeed, the suggested limits can be increased to handle bigger graphs.
- When loading external graphs nodes MUST be identified by integer ids.
