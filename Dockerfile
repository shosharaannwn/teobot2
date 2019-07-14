FROM alpine:latest

RUN apk add --no-cache python3

COPY requirements.txt /

RUN pip3 install -r requirements.txt

COPY teo_bot2.py /

RUN adduser -D teobot
RUN mkdir -p /var/google_sheet_pickle
RUN chown teobot /var/google_sheet_pickle

ENTRYPOINT /teo_bot2.py


