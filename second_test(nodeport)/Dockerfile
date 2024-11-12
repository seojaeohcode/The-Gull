"""
# Dockerfile
# Python 3.11.0 기반 이미지 사용
FROM python:3.11.0

# 필요한 패키지 설치 (envsubst 포함)
RUN apt-get update && apt-get install -y gettext curl

# Python의 UTF-8 인코딩 설정
ENV PYTHONIOENCODING=utf-8

# 작업 디렉토리 설정
WORKDIR /project

# kubectl 설치
RUN curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl" && \
    chmod +x kubectl && \
    mv kubectl /usr/local/bin/

# 로컬의 /project/slack_test.py 파일을 컨테이너의 /project 디렉토리에 복사
COPY /project/slack_test.py /project/slack_test.py
    
# 필요한 파일들을 /project 디렉토리에 복사
COPY .env /project/.env
COPY deploy.sh /project/deploy.sh
COPY service-account.yaml /project/service-account.yaml
COPY deployment.yaml /project/deployment.yaml
COPY service.yaml /project/service.yaml
COPY network_update.yaml /project/network_update.yaml
COPY init.yaml /project/init.yaml

# deploy.sh에 실행 권한 부여
RUN chmod +x /project/deploy.sh

# requirements.txt 파일 복사 및 종속성 설치
COPY requirements.txt ./ 
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Flask 애플리케이션 자동 실행
CMD ["flask", "run"]
"""