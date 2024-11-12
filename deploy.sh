#!/bin/bash

# Step 1: 초기 ConfigMap 설정을 위한 init.yaml 적용
echo "Applying initial configuration using init.yaml..."
kubectl apply -f /project/init.yaml --validate=false

# Step 2: Localtunnel을 통해 터널링 설정
echo "Starting Localtunnel to tunnel the Flask application..."
lt --port 30007 > tunnel.log 2>&1 &
LT_PID=$!

# Localtunnel이 시작되기를 기다림
sleep 5

# Localtunnel URL 확인
lt_url=$(grep -o 'https://.*' tunnel.log | head -n 1)

if [ -z "$lt_url" ]; then
    echo "Failed to start Localtunnel. Check tunnel.log for details."
    exit 1
else
    echo "Localtunnel started successfully. URL: $lt_url"
fi

# Step 3: .env 파일을 ConfigMap으로 생성 또는 업데이트
echo "Creating/updating ConfigMap from .env file..."
kubectl create configmap app-env --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f - --validate=false

# Step 4: IP 갱신을 위한 Kubernetes CronJob 설정
echo "Setting up Kubernetes CronJob for IP update..."
kubectl apply -f /project/network_update.yaml

# Step 5: Kubernetes 리소스 적용 (Service 및 Deployment)
echo "Applying Kubernetes configurations for deployment and service..."
kubectl apply -f /project/deployment.yaml --validate=false || echo "deployment.yaml not found, skipping..."
kubectl apply -f /project/service.yaml --validate=false || echo "service.yaml not found, skipping..."

# Localtunnel URL 출력
echo "Your Localtunnel URL is: $lt_url"

echo "Deployment completed successfully!"

# 스크립트가 종료되지 않도록 Localtunnel 프로세스를 기다림
wait $LT_PID