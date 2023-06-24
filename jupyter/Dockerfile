FROM tensorflow/tensorflow:latest-gpu-jupyter

RUN pip install opencv-python
RUN pip install pycocotools
RUN pip install keras-cv
RUN adduser --uid 1000 --disabled-password --gecos "" myuser
USER myuser

WORKDIR /ibkr

COPY requirements.txt /ibkr
RUN pip3 install -r requirements.txt

COPY . /ibkr

EXPOSE 8888

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--no-browser", "--allow-root"]
