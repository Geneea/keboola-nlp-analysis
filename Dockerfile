# VERSION 1.0.1

FROM quay.io/keboola/docker-custom-python:1.1.3
MAINTAINER Tomáš Mudruňka <mudrunka@geneea.com>

# setup the environment
WORKDIR /tmp
RUN pip install requests

# prepare the container
WORKDIR /home
COPY src src/

ENTRYPOINT python ./src/main.py --data=/data
