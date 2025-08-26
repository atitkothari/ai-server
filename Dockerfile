FROM python:3.11
ENV TZ=Asia/Kolkata
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN apt-get -y update && apt-get install -y --no-install-recommends \
         wget \
         git \
         libgl1 \
         libgtk2.0-dev \
         python3-setuptools \
         nginx \
         ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# Install system deps.
RUN apt-get -y update && apt-get install ffmpeg libsm6 libxext6  -y
# Copy the AWS Permission directory (TODO: Remove this in the future)
ADD .aws /root/.aws
# Copy the local repository
ADD ai-server ai-server
WORKDIR ai-server
# Install dependencies
RUN pip install -r requirements.txt
# Commands to run
# ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--workers", "1"]
