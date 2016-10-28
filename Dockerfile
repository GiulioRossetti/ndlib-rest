FROM python:2.7-slim
MAINTAINER Salvo Rinzivillo <rinzivillo@isti.cnr.it>
COPY . /app
WORKDIR /app
RUN pip install --upgrade pip 
RUN pip install gunicorn
RUN pip install -r requirements.txt

EXPOSE 5000

ENTRYPOINT ["/bin/bash"]
CMD ["gunicorn.sh"]
