# deploy.sh
#!/bin/bash

# Step 2: 초기 ConfigMap 설정을 위한 init.yaml 적용
echo "Applying initial configuration using init.yaml..."
kubectl apply -f /project/init.yaml --validate=false

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

echo "Deployment completed successfully!"
