#!/bin/bash

# Step 1: MetalLB 및 Ingress Controller 설정
echo "Applying Ingress Controller configurations..."
kubectl apply -f /project/ingress-nginx-controller.yaml

# Step 2: .env 파일을 ConfigMap으로 생성 또는 업데이트
echo "Creating/updating ConfigMap from .env file..."
kubectl create configmap app-env --from-env-file=.env --dry-run=client -o yaml | kubectl apply -f - --validate=false

# ConfigMap에서 DOMAIN 값 가져오기
DOMAIN=$(kubectl get configmap app-env -o jsonpath='{.data.DOMAIN}')
export DOMAIN

# Step 3: init.yaml 적용
echo "Applying initial DDNS update job with init.yaml..."
kubectl apply -f /project/init.yaml --validate=false

# Step 4: Kubernetes 리소스 적용
echo "Applying Kubernetes configurations..."
kubectl apply -f /project/secret.yaml --validate=false || echo "secret.yaml not found, skipping..."
kubectl apply -f /project/deployment.yaml --validate=false || echo "deployment.yaml not found, skipping..."
kubectl apply -f /project/service.yaml --validate=false || echo "service.yaml not found, skipping..."

# Step 5: Ingress 적용
echo "Applying Ingress with substituted DOMAIN..."
envsubst < /project/ingress.yaml | kubectl apply -f - || echo "ingress.yaml not found, skipping..."

# Step 6: frp 터널링 시작
echo "Starting frp tunnel..."
/usr/local/bin/frpc -c /project/frpc.ini &

# Step 7: 주기적인 IP 갱신 cronjob 설정
echo "Setting up cronjob for public IP update..."
(crontab -l ; echo "*/15 * * * * /usr/local/bin/frpc -c /project/frpc.ini") | crontab -

echo "All configurations applied successfully!"
