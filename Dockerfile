# Dockerfile
# Python 3.11.0 기반 이미지 사용
FROM python:3.11.0

# Python의 UTF-8 인코딩 설정
ENV PYTHONIOENCODING=utf-8

# NGINX 설치를 위한 패키지 설치
#RUN apt-get update && \
#    apt-get install -y nginx && \
#    apt-get clean && \
#    rm -rf /var/lib/apt/lists/*

# 작업 디렉토리 설정
WORKDIR /project

# 로컬의 /project/slack_test.py 파일을 컨테이너의 /project 디렉토리에 복사
COPY /project/slack_test.py /project/slack_test.py
COPY .env /project/.env

# requirements.txt 파일 복사 및 종속성 설치
COPY requirements.txt ./ 
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# NGINX 및 Gunicorn을 사용해 Flask 애플리케이션 실행
#CMD ["sh", "-c", "service nginx start && gunicorn --bind 0.0.0.0:5000 slack_test:app"]

# Flask 애플리케이션 자동 실행
CMD ["flask", "run"]