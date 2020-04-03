FROM python:3

RUN apt-get update && \
    apt-get install -y libsecp256k1-dev && \
    apt-get install -y cmake

COPY python /python
RUN pip install -r /python/requirements.txt

COPY trezor /trezor
RUN mkdir /trezor/build && \
    cd /trezor/build && \
    cmake ../ && \
    make

CMD /bin/bash
