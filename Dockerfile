FROM alpine:latest

RUN apk add --no-cache python3

COPY requirements.txt /

RUN pip3 install -r requirements.txt

COPY teo_bot2.py /

ENTRYPOINT /teo_bot2.py



