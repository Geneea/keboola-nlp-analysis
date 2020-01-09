# VERSION 2.6.2

FROM quay.io/keboola/docker-custom-python:1.5.12
MAINTAINER Tomáš Mudruňka <mudrunka@geneea.com>

# prepare the container
WORKDIR /home
COPY src src/

ENTRYPOINT python ./src/main.py --data=/data
