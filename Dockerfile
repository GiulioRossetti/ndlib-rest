FROM nikolaik/python-nodejs:latest

MAINTAINER Giulio Rossetti <giulio.rossetti@gmail.com>

COPY requirements.txt /tmp/

RUN pip install --upgrade pip
RUN pip install gunicorn
RUN pip install -r /tmp/requirements.txt
RUN apt-get update
RUN apt-get -y install git

COPY . /app
WORKDIR /app

RUN git clone https://github.com/GiulioRossetti/NDLib_viz.git

WORKDIR NDLib_viz
RUN npm install

EXPOSE 5000 8080

WORKDIR /app
ENTRYPOINT ["/bin/bash"]
CMD ["gunicorn.sh"]
