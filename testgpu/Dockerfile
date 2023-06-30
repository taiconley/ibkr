docker pull datamachines/cuda_tensorflow_opencv

FROM datamachines/cuda_tensorflow_opencv

COPY . /ibkr

datamachines/cudnn_tensorflow_opencv:11.6.2_2.9.1_4.6.0-20220815

docker run -it --gpus all datamachines/cudnn_tensorflow_opencv:11.6.2_2.9.1_4.6.0-20220815 bash

#if docker run hello-world doesn't work
docker -H unix:///var/run/docker.sock run hello-world
alias docker='docker -H unix:///var/run/docker.sock'
source ~/.bashrc
