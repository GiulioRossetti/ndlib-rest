# ndlib-rest
Network Diffusion Library REST Service.

This project offers a REST interface for the [[ndlib|https://github.com/GiulioRossetti/ndlib]] Python library.


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
- flask_shelve
- flask_restful
- flask_apidoc
- networkx
- numpy

#### REST service setup
Local testing
```python
    python ndrest.py
```

Local testig with multiple workers (using [[gunicorn|http://gunicorn.org/]] web server):
```bash
    gunicorn -w num_workers -b 127.0.0.1:5000 ndrest:app
```

In order to change the binding IP/port modify the apidoc.json file.
To update the API page run the command:
```
    apidoc -i ndlib-rest/ -o ndlib-rest/static/docs
```
