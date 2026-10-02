# K8s 微服务全链路监控告警与 CI/CD 平台

## 项目简介

在自建 K8s 集群上部署 Flask + MySQL + Redis 微服务，配套 Ingress、Prometheus、Grafana、Alertmanager、ELK、Jenkins、Harbor、Chaos Mesh、AIOps，覆盖生产环境核心运维能力。

## 技术栈

- 容器编排：Kubernetes、Docker、Helm
- 应用：Flask、MySQL、Redis
- 入口：Ingress-Nginx
- 监控：Prometheus、Grafana、Alertmanager
- 日志：ELK（Elasticsearch、Kibana、Filebeat）
- CI/CD：Jenkins、Harbor
- 混沌：Chaos Mesh
- 压测：k6
- 脚本：Shell、Python

## 架构

浏览器 → Ingress → Flask Service → Flask Pod ×2
                                    ↓
                              MySQL Service → MySQL Pod → PVC
                              Redis Service → Redis Pod

监控：Prometheus → Grafana / Alertmanager → 钉钉
日志：Filebeat → Elasticsearch → Kibana
CI/CD：GitHub → Jenkins → Harbor → K8s
混沌：Chaos Mesh → Flask Pod
AIOps：Alertmanager → Webhook → DeepSeek → 钉钉

## 微服务部署

- 在 K8s 上部署 Flask + MySQL + Redis 微服务
- Flask 提供 /health、/db、/redis、/metrics 四个接口
- MySQL 用 Secret 存密码、PVC 持久化、Headless Service 给固定 DNS
- Redis 用 Deployment + Service
- Flask 用 ConfigMap 注入配置、2 副本、liveness/readiness 探针
- 脚本：scripts/k8s-deploy.sh

## Ingress 七层入口

- 装 ingress-nginx
- 写 Ingress，按域名 flask.local 转发到 Flask Service

## 故障排查

模拟并排查 5 种 K8s 常见故障：

| 故障 | 现象 | 根因 | 解决 |
|---|---|---|---|
| ImagePullBackOff | Pod 拉镜像失败 | 镜像 tag 不存在 | 改回正确 tag |
| CrashLoopBackOff | Pod 反复重启 | 探针路径 404 | 改回 /health |
| OOMKilled | Pod 被内核杀 | limits.memory 太小 | 调大 limit |
| Service 不通 | Endpoints 为空 | selector 不匹配 | 改回 app=flask |
| Pending | Pod 不调度 | requests.cpu 过大 | 改成 100m |

脚本：scripts/k8s-pod-doctor.py

## 监控告警

- Helm 部署 kube-prometheus-stack
- ServiceMonitor 自动发现 Flask 指标
- 写 PromQL 查询 CPU、内存、QPS、P95
- 4 条告警规则：FlaskPodDown、FlaskHighCPU、FlaskHighMemory、FlaskPodRestarting
- Alertmanager 分级路由 + 钉钉通知
- 5 个 Grafana 面板
- SLI/SLO + Runbook 文档
- 脚本：scripts/prom_query.py、scripts/dingtalk_alert.py

## CI/CD 流水线

- 部署 Harbor 私有镜像仓库
- 三台节点配 insecure-registries
- Flask 镜像推到 Harbor
- Jenkins Pipeline 五个 stage：拉代码、构建镜像、推 Harbor、部署 K8s、验证
- 部署时间从 20 分钟缩短到 5 分钟
- 脚本：scripts/jenkins_trigger.py

## 日志采集

- Docker Compose 搭 Filebeat + Elasticsearch + Kibana
- 采集所有容器日志
- Kibana 创建 Data View，按容器名、时间、关键词检索
- 脚本：scripts/nginx_log_top.py

## 压测与混沌工程

- k6 压测 Flask，观察 QPS、延迟、错误率，验证 HPA 扩容
- HPA 从 2 个 Pod 扩到 10 个
- Chaos Mesh 杀 Pod，验证 K8s 自愈
- 脚本：scripts/chaos_kill_pod.sh

## AIOps 告警智能分析

- 搭 AIOps 闭环：Prometheus → Alertmanager → Webhook → DeepSeek → 钉钉
- 告警触发后自动调 LLM 分析，输出根因、排查命令、修复建议
- 服务代码：aiops/app.py

## 目录结构

sre-project/
├── app.py
├── requirements.txt
├── Dockerfile
├── Jenkinsfile
├── README.md
├── aiops/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── elk/
│   ├── docker-compose.yaml
│   └── filebeat.yml
├── k6/
│   └── test.js
├── k8s/
│   ├── mysql-secret.yaml
│   ├── mysql-pvc.yaml
│   ├── mysql-deployment.yaml
│   ├── mysql-service.yaml
│   ├── redis-deployment.yaml
│   ├── redis-service.yaml
│   ├── flask-configmap.yaml
│   ├── flask-deployment.yaml
│   ├── flask-service.yaml
│   ├── flask-ingress.yaml
│   ├── flask-servicemonitor.yaml
│   ├── flask-alert-rules.yaml
│   ├── flask-hpa.yaml
│   ├── alertmanager-config.yaml
│   ├── dingtalk-adapter.yaml
│   └── chaos-kill-pod.yaml
├── scripts/
│   ├── k8s-deploy.sh
│   ├── k8s-pod-doctor.py
│   ├── prom_query.py
│   ├── dingtalk_alert.py
│   ├── jenkins_trigger.py
│   ├── nginx_log_top.py
│   ├── chaos_kill_pod.sh
│   └── ai_pod_doctor.py
└── docs/
    ├── slo.md
    └── runbook.md
