FROM alpine:latest

RUN apk add --no-cache python3 tzdata

RUN cp /usr/share/zoneinfo/America/Los_Angeles /etc/localtime

COPY requirements.txt /
RUN pip3 install -r requirements.txt

COPY teo_bot2.py teo_bot2_config.py teo_bot2_config_test.py /

RUN adduser -D teobot
RUN mkdir -p /var/google_sheet_pickle
RUN chown teobot /var/google_sheet_pickle

ENTRYPOINT /teo_bot2.py -c teo_bot2_config.py
