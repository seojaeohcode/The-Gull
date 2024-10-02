# Python 3.12.6 기반 이미지 사용
FROM python:3.12.6

# Python의 UTF-8 인코딩 설정
ENV PYTHONIOENCODING=utf-8

# 작업 디렉토리 설정
WORKDIR /project

# 루트 경로에 있는 requirements.txt 파일 복사
COPY requirements.txt ./

# pip 업그레이드 및 종속성 설치
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# project 폴더의 모든 코드 파일 및 폴더 복사
COPY project/ ./

# Flask 환경 변수 설정
ENV FLASK_APP=slack_test.py
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# 컨테이너 실행 시 아무것도 실행하지 않음 (원할 때 실행)
CMD ["tail", "-f", "/dev/null"]

# Flask 서버 실행
#CMD ["flask", "run"]