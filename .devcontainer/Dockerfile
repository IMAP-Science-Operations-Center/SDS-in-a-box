# OS
ARG VARIANT=bullseye
FROM --platform=linux/amd64 mcr.microsoft.com/vscode/devcontainers/base:0-${VARIANT}
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive && apt-get install -y firefox-esr
RUN sudo apt-get update
RUN sudo apt-get install -y libgtk-3-dev
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs
RUN npm install -g aws-cdk
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
RUN unzip awscliv2.zip
RUN sudo ./aws/install
RUN sudo apt-get install -y python3 python3-pip
RUN pip install aws-cdk-lib==2.48.0 
RUN pip install "constructs>=10.0.0,<11.0.0"
RUN pip install boto3
RUN pip install requests
RUN pip install python-jose
ENV AWS_CONFIG_FILE=/workspaces/SDS-in-a-box/.aws/config
ENV AWS_SHARED_CREDENTIALS_FILE=/workspaces/SDS-in-a-box/.aws/credentials