FROM python:3

RUN apt-get update && \
    apt-get install -y libsecp256k1-dev && \
    pip install secp256k1 && \
    pip install pycoin

COPY python/decv.py /python/decv.py

CMD /bin/bash
