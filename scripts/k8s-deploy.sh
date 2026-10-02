#!/bin/bash
set -euo pipefail

NAMESPACE=${1:-sre-project}
echo "[$(date)] 部署到 namespace: $NAMESPACE"

kubectl apply -f k8s/ -n "$NAMESPACE"

echo "[$(date)] 等待 Flask Pod 就绪..."
kubectl wait --for=condition=Ready pods -l app=flask -n "$NAMESPACE" --timeout=180s

echo "[$(date)] Pod 状态:"
kubectl get pods -n "$NAMESPACE" -o wide

echo "[$(date)] Service 状态:"
kubectl get svc -n "$NAMESPACE"

echo "[$(date)] 部署完成"
