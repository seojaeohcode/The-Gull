#!/bin/bash

# .env 파일 로드
source /project/.env

# DDNS 업데이트 URL 설정
update_url="http://freedns.afraid.org/dynamic/update.php?$YOUR_SECRET_KEY"

# IP 주소 저장 파일 위치
ip_file="/tmp/current_ip.txt"

# NGINX Ingress Controller 네임스페이스 및 서비스 이름
namespace="ingress-nginx"
service_name="ingress-nginx-controller"

# 네트워크 변경 감지 및 DDNS 업데이트 백그라운드 작업
while true; do
    # Ingress Controller의 공용 IP 가져오기
    current_ip=$(kubectl get service $service_name -n $namespace -o jsonpath="{.status.loadBalancer.ingress[0].ip}")

    # 공용 IP가 설정되지 않은 경우, 잠시 대기 후 다시 확인
    if [ -z "$current_ip" ]; then
        echo "Waiting for Ingress Controller to get a public IP..."
        sleep 300
        continue
    fi

    # IP 파일이 없으면 새로 생성하고 DDNS 업데이트 호출
    if [ ! -f "$ip_file" ]; then
        echo "$current_ip" > "$ip_file"
        curl -s "$update_url"
        echo "DDNS 업데이트 URL 호출 완료 (초기 설정)"
    else
        # 기존 IP와 비교하여 변경 시 업데이트
        previous_ip=$(cat "$ip_file")
        if [ "$current_ip" != "$previous_ip" ]; then
            echo "$current_ip" > "$ip_file"
            curl -s "$update_url"
            echo "DDNS 업데이트 URL 호출 완료 (IP 변경 감지)"
        else
            echo "IP 변경 없음: $current_ip"
        fi
    fi

    # 대기 시간 설정 (예: 10초)
    sleep 10
done
