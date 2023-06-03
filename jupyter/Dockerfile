FROM tensorflow/tensorflow:latest-gpu-jupyter

WORKDIR /jupyter

COPY requirements.txt /jupyter
RUN pip3 install -r requirements.txt

COPY . /jupyter

EXPOSE 8888
WORKDIR /root

CMD ["jupyter", "notebook", "--ip=0.0.0.0", "--no-browser", "--allow-root"]