from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

LLM_API = "https://api.deepseek.com/v1/chat/completions"
LLM_KEY = os.getenv("LLM_API_KEY", "")
DINGTALK_WEBHOOK = os.getenv("DINGTALK_WEBHOOK", "")

def analyze_alert(alert):
    name = alert.get("labels", {}).get("alertname", "")
    namespace = alert.get("labels", {}).get("namespace", "")
    summary = alert.get("annotations", {}).get("summary", "")
    description = alert.get("annotations", {}).get("description", "")

    prompt = f"""你是 K8s SRE 专家。分析这个告警，给出：
1. 可能原因（2-3 条）
2. 排查命令（具体 kubectl 命令）
3. 修复建议

告警信息：
- 名称：{name}
- 命名空间：{namespace}
- 摘要：{summary}
- 描述：{description}

回答简洁，直接给命令和步骤。"""

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

def send_dingtalk(text):
    if not DINGTALK_WEBHOOK:
        print("[!] 没配钉钉 webhook")
        return
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": "AIOps 告警分析", "text": text}
    }
    requests.post(DINGTALK_WEBHOOK, json=payload, timeout=10)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    alerts = data.get("alerts", [])
    print(f"[*] 收到 {len(alerts)} 条告警")

    for alert in alerts:
        if alert.get("status") != "firing":
            continue
        name = alert.get("labels", {}).get("alertname", "")
        print(f"[*] 分析告警: {name}")
        try:
            analysis = analyze_alert(alert)
            text = f"## AIOps 告警分析\n\n**告警**: {name}\n\n{analysis}"
            send_dingtalk(text)
            print(f"[+] 已推送: {name}")
        except Exception as e:
            print(f"[-] 分析失败: {e}")

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
