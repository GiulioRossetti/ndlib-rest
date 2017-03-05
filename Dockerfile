FROM python:2.7-slim
MAINTAINER Salvo Rinzivillo <rinzivillo@isti.cnr.it>


COPY requirements.txt /tmp/



RUN pip install --upgrade pip 
RUN pip install gunicorn
RUN pip install -r /tmp/requirements.txt


COPY . /app
WORKDIR /app

EXPOSE 5000

ENTRYPOINT ["/bin/bash"]
CMD ["gunicorn.sh"]
