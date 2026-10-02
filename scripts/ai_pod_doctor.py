#!/usr/bin/env python3
import subprocess
import sys
import requests
import os

LLM_API = "https://api.deepseek.com/v1/chat/completions"
LLM_KEY = os.getenv("LLM_API_KEY", "")

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

def collect_info(pod_name, namespace="sre-project"):
    events = run(f"kubectl describe pod {pod_name} -n {namespace} | tail -30")
    logs = run(f"kubectl logs {pod_name} -n {namespace} --previous 2>/dev/null | tail -30")
    if not logs.strip():
        logs = run(f"kubectl logs {pod_name} -n {namespace} | tail -30")
    status = run(f"kubectl get pod {pod_name} -n {namespace} -o wide")
    return f"状态:\n{status}\n\nEvents:\n{events}\n\n日志:\n{logs}"

def ask_llm(info):
    prompt = f"""你是 K8s 运维专家。分析这个 Pod 的故障，给出：
1. 根因分析
2. 修复步骤
3. 预防措施

Pod 信息：
{info}
"""
    resp = requests.post(LLM_API,
        headers={"Authorization": f"Bearer {LLM_KEY}", "Content-Type": "application/json"},
        json={
            "model": "deepseek-chat",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        },
        timeout=60
    )
    return resp.json()["choices"][0]["message"]["content"]

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python3 ai_pod_doctor.py <pod名>")
        sys.exit(1)
    pod = sys.argv[1]
    print(f"[*] 收集 {pod} 信息...")
    info = collect_info(pod)
    print(f"[*] 调用 AI 分析...")
    result = ask_llm(info)
    print("\n=== AI 诊断结果 ===\n")
    print(result)
