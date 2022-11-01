FROM gitpod/workspace-full-vnc
RUN sudo apt-get update && \
    sudo apt-get install -y libgtk-3-dev && \
    sudo rm -rf /var/lib/apt/lists/* \
    sudo apt-get install libxcb-xinerama0
RUN sudo apt-get -y install libsm6 
RUN sudo apt install -y nodejs
RUN npm install -g aws-cdk