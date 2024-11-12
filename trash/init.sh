#!/bin/bash

# 현재 KUBECONFIG 설정 및 추가된 환경 변수 확인
echo "Current KUBECONFIG settings:"
kubectl config view

# 환경 변수 확인
echo "Setting environment variables..."
export KUBECONFIG=~/.kube/config
export CLUSTER_NAME="local-cluster"

# .env 파일 로드
source /project/.env || {
    echo "Failed to load environment variables from .env"
    exit 1
}

# 확인용 추가 환경 변수 출력
echo "Environment variables loaded:"
echo "KUBE_API_SERVER: $KUBE_API_SERVER"
echo "DDNS_SECRET_KEY: $YOUR_SECRET_KEY"
echo "KUBECONFIG: $KUBECONFIG"
echo "CLUSTER_NAME: $CLUSTER_NAME"

# 기존 Kubeconfig 병합 확인
if [[ -f ~/.kube/config ]]; then
    echo "Existing kubeconfig detected, attempting to merge configurations..."
    export KUBECONFIG=~/.kube/config:$KUBECONFIG
    kubectl config view --merge --flatten > /tmp/config && mv /tmp/config ~/.kube/config
fi

# 기존 default-token 시크릿 삭제 및 새로운 시크릿 생성
echo "Checking for existing default-token secrets and removing..."
kubectl delete secret -n default default-token --ignore-not-found

echo "Creating new token secret for default ServiceAccount..."
kubectl apply -f - <<EOF
apiVersion: v1
kind: Secret
metadata:
  name: default-token
  annotations:
    kubernetes.io/service-account.name: "default"
type: kubernetes.io/service-account-token
EOF

# 토큰 시크릿이 생성될 때까지 기다림
sleep 5

# ServiceAccount 토큰 및 CA 인증서 가져오기 및 검증
echo "Fetching token and CA certificate for default ServiceAccount..."
KUBE_API_TOKEN=$(kubectl get secret default-token -o jsonpath='{.data.token}' | base64 -d 2>/dev/null)
if [[ -z "$KUBE_API_TOKEN" ]]; then
    echo "Failed to retrieve the token for ServiceAccount. Exiting."
    exit 1
fi

kubectl get secret default-token -o jsonpath='{.data.ca\.crt}' | base64 -d > ~/.kube/ca.crt
if [[ ! -s ~/.kube/ca.crt ]]; then
    echo "Failed to retrieve CA certificate. Exiting."
    exit 1
fi

# kubeconfig 파일 설정 초기화 후 클러스터 및 사용자 설정
echo "Configuring kubeconfig with server details, ServiceAccount token, and CA certificate..."
kubectl config unset users.default-user
kubectl config unset contexts.local-context
kubectl config set-cluster "$CLUSTER_NAME" --server="$KUBE_API_SERVER" --certificate-authority=~/.kube/ca.crt --embed-certs=true
kubectl config set-credentials default-user --token="$KUBE_API_TOKEN"
kubectl config set-context local-context --cluster="$CLUSTER_NAME" --namespace=default --user=default-user
kubectl config use-context local-context

echo "Updated kubeconfig file contents:"
kubectl config view

# default ServiceAccount에 cluster-admin 권한 부여 및 검증
echo "Setting cluster role binding for default service account..."
kubectl create clusterrolebinding default-service-account-binding --clusterrole=cluster-admin --serviceaccount=default:default || {
    echo "Error creating cluster role binding for default service account"
    exit 1
}
kubectl auth can-i create pods --as=system:serviceaccount:default:default || {
    echo "Cluster role binding validation failed"
    exit 1
}

# DDNS 업데이트 URL 설정
update_url="http://freedns.afraid.org/dynamic/update.php?$YOUR_SECRET_KEY"

# DDNS 업데이트 URL 호출
echo "클러스터 시작 - DDNS 업데이트 URL 호출 중..."
curl -s "$update_url" || {
    echo "Failed to update DDNS URL"
    exit 1
}
echo "DDNS 업데이트 URL 호출 완료."

# ConfigMap 생성
echo "Checking and creating ConfigMaps..."
kubectl create configmap app-env --from-env-file=.env -n default --dry-run=client -o yaml | kubectl apply -f - || {
    echo "Failed to create app-env ConfigMap"
    exit 1
}

kubectl create configmap ddns-script --from-file=ddns_update.sh -n default --dry-run=client -o yaml | kubectl apply -f - || {
    echo "Failed to create ddns-script ConfigMap"
    exit 1
}

# NGINX Ingress Controller 설치
echo "Installing NGINX Ingress Controller..."
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/cloud/deploy.yaml || {
    echo "Failed to apply NGINX Ingress deployment"
    exit 1
}

echo "Waiting for NGINX Ingress Controller to be ready..."
kubectl rollout status deployment ingress-nginx-controller -n ingress-nginx || {
    echo "NGINX Ingress Controller deployment failed. Exiting."
    exit 1
}

# Ingress Controller 외부 IP 확인 및 FreeDNS 설정 안내
echo "Checking NGINX Ingress external IP..."
ingress_ip=""
retry_count=0
while [[ -z "$ingress_ip" && $retry_count -lt 5 ]]; do
    sleep 10
    ingress_ip=$(kubectl get svc ingress-nginx-controller -o jsonpath="{.status.loadBalancer.ingress[0].ip}" -n ingress-nginx)
    retry_count=$((retry_count + 1))
    echo "Retrying external IP retrieval... Attempt: $retry_count"
done

if [[ -z "$ingress_ip" ]]; then
    echo "Failed to retrieve Ingress IP. Please check manually."
else
    echo "Ingress Controller External IP: $ingress_ip"
    echo "Please set this IP in your FreeDNS configuration for the domain to enable external access."
fi