FROM python:latest

RUN cp /usr/share/zoneinfo/America/Los_Angeles /etc/localtime

COPY requirements.txt /tmp
RUN python3 -m pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

COPY aioschedule-0.5.2+teobot-py3-none-any.whl /
RUN python3 -m pip install aioschedule-0.5.2+teobot-py3-none-any.whl

COPY teo_bot2.py teo_bot2_config.py teo_bot2_config_test.py /

RUN adduser --disabled-password teobot

ENTRYPOINT /teo_bot2.py -c teo_bot2_config.py