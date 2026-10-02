# K8s 微服务全链路监控告警与 CI/CD 平台

## 项目简介
在 K8s 上部署 Flask + MySQL + Redis 微服务，配套 Ingress、Prometheus、Grafana、Alertmanager、Jenkins、Harbor，实现生产级可观测性和自动化。

## 架构
浏览器 → Ingress → Flask Service → Flask Pod ×2
                                    ↓
                              MySQL Service → MySQL Pod → PVC
                              Redis Service → Redis Pod

监控：Prometheus → Grafana / Alertmanager → 钉钉
CI/CD：GitHub → Jenkins → Harbor → K8s

## 技术栈
- 容器编排：Kubernetes、Docker、Helm
- 应用：Flask、MySQL、Redis
- 入口：Ingress-Nginx
- 监控：Prometheus、Grafana、Alertmanager
- CI/CD：Jenkins、Harbor
- 脚本：Shell、Python

## Day 1：微服务部署
- Flask + MySQL + Redis 部署到 K8s
- ConfigMap、Secret、PVC、探针
- /health、/db、/redis 验证通过
- 脚本：k8s-deploy.sh

## Day 2：Ingress 与故障排查
- 装 ingress-nginx，写 Ingress，按域名转发
- 模拟并排查 5 种故障：
  - ImagePullBackOff：镜像 tag 不存在
  - CrashLoopBackOff：探针路径 404
  - OOMKilled：limits.memory 太小
  - Service 不通：selector 不匹配
  - Pending：requests.cpu 过大
- 脚本：k8s-pod-doctor.py

## Day 3：监控告警
- Helm 装 kube-prometheus-stack
- ServiceMonitor 自动发现 Flask 指标
- 写 PromQL 查询 CPU、内存、QPS、P95
- 4 条告警规则：FlaskPodDown、FlaskHighCPU、FlaskHighMemory、FlaskPodRestarting
- Alertmanager 分级路由 + 钉钉通知
- 5 个 Grafana 面板
- SLI/SLO + Runbook 文档
- 脚本：prom_query.py、dingtalk_alert.py

## Day 4：CI/CD 流水线
- 部署 Harbor 私有镜像仓库
- 三台节点配 insecure-registries
- Flask 镜像推到 Harbor
- Jenkins Pipeline 五个 stage：拉代码、构建镜像、推 Harbor、部署 K8s、验证
- 部署时间从 20 分钟缩短到 5 分钟
- 脚本：jenkins_trigger.py

## 目录结构
sre-project/
├── app.py
├── requirements.txt
├── Dockerfile
├── Jenkinsfile
├── README.md
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
│   ├── alertmanager-config.yaml
│   └── dingtalk-adapter.yaml
├── scripts/
│   ├── k8s-deploy.sh
│   ├── k8s-pod-doctor.py
│   ├── prom_query.py
│   ├── dingtalk_alert.py
│   └── jenkins_trigger.py
└── docs/
    ├── slo.md
    └── runbook.md

## 故障排查记录
| 故障 | 现象 | 根因 | 解决 |
|---|---|---|---|
| ImagePullBackOff | Pod 拉镜像失败 | 镜像 tag 不存在 | 改回正确 tag |
| CrashLoopBackOff | Pod 反复重启 | 探针路径 404 | 改回 /health |
| OOMKilled | Pod 被内核杀 | limits.memory 太小 | 调大 limit |
| Service 不通 | Endpoints 为空 | selector 不匹配 | 改回 app=flask |
| Pending | Pod 不调度 | requests.cpu 过大 | 改成 100m |

## 面试要点
- K8s 存储链路：PVC → StorageClass → provisioner → helper pod → PV → Pod
- 生产私有仓库：Harbor，节点预拉，避免公网依赖
- 监控三支柱：Metrics（Prometheus）、Logs（ELK）、Traces
- CI/CD：Jenkins Pipeline + 滚动更新
- 告警设计坑：up == 0 在 target 消失时不触发，要用 kube-state-metrics 指标

## Day 5：ELK + k6 + Chaos Mesh
- Docker Compose 搭 Filebeat + Elasticsearch + Kibana，采集容器日志
- Kibana 创建 Data View，查日志
- k6 压测 Flask，HPA 从 2 个 Pod 扩到 10 个
- Chaos Mesh 杀 Pod，验证 K8s 自愈
- 脚本：nginx_log_top.py、chaos_kill_pod.sh
- k6 脚本：k6/test.js
- ELK 配置：elk/docker-compose.yaml、elk/filebeat.yml
