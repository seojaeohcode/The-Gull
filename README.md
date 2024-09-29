# The-Gull
데굴

# Docker 사용 가이드
---
## 1. 프로젝트 루트 디렉토리로 이동(CMD)
```bash
cd /path/to/your/project
```
## 2. Docker 이미지 빌드
```bash
# 빌드
docker-compose build
```
## 3. Docker 컨테이너 실행
```bash
# 컨테이너 실행
docker-compose up -d
# 실행 중인 컨테이너 상태 확인
docker-compose ps
```
## 4. 컨테이너 내부에 접근
```bash
# 컨테이너 내부 진입
docker exec -it <container_name> /bin/bash
```
## 5. Flask 애플리케이션 실행
```bash
flask run
```
## 6. 컨테이너 종료
```bash
# 종료시켜야할 컨테이너 id 체크
docker ps
# 종료
docker stop <container_id>
# 종료되었는지 확인
docker ps -a
```
## 7. 패키지 관리(각자 필요한 패키지 설치 후 한 번에 병합) 
```bash
# 컨테이너에 접속
docker exec -it <container_name> /bin/bash
# 설치된 패키지 목록 확인
pip list
```
