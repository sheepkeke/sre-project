# Day 2 故障排查记录

## 故障一：ImagePullBackOff

**现象：** Pod 状态从 ContainerCreating 变成 ErrImagePull，再变成 ImagePullBackOff。

**改什么：**

`k8s/flask-deployment.yaml`

```yaml
image: sre-flask:v999
```

**执行的命令：**

```bash
vim k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期结果：**

```text
NAME                     READY   STATUS             RESTARTS   AGE
flask-xxxxx-xxxxx        0/1     ContainerCreating  0          5s
flask-xxxxx-xxxxx        0/1     ErrImagePull       0          30s
flask-xxxxx-xxxxx        0/1     ImagePullBackOff   0          60s
```

**这代表什么：** 正常应该是 `1/1 Running`。出现 `ErrImagePull` / `ImagePullBackOff` 说明 kubelet 拉镜像失败，Pod 无法启动。需要排查镜像名、tag、仓库认证、网络。

**排查命令：**

```bash
kubectl describe pod <新flask-pod> | tail -20
```

**预期排查结果：**

```text
Events:
  Type     Reason     Age                From      Message
  ----     ------     ----               ----      -------
  Warning  Failed     30s (x3 over 60s)  kubelet   Failed to pull image "sre-flask:v999": rpc error: code = NotFound desc = manifest unknown
  Warning  Failed     30s (x3 over 60s)  kubelet   Error: ErrImagePull
  Warning  Failed     30s (x3 over 60s)  kubelet   Error: ImagePullBackOff
```

**这代表什么：** Events 写 `Failed to pull image` 加 `manifest unknown`，说明仓库里没有这个 tag。正常应该显示 `Pulled` 成功。问题是 tag 写错。

**根因：** 镜像 tag v999 不存在，本地和仓库都没有。

**解决：**

```bash
vim k8s/flask-deployment.yaml
# 把 image: sre-flask:v999 改回 image: sre-flask:v1

kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期恢复结果：**

```text
NAME                     READY   STATUS    RESTARTS   AGE
flask-xxxxx-xxxxx        1/1     Running   0          30s
```

**面试描述：** 生产遇到过 ImagePullBackOff，先 `kubectl describe pod` 看 Events，区分镜像名错、仓库认证失败、网络不通。镜像名错就改 tag，私有仓库检查 imagePullSecrets，网络问题检查节点到仓库的连通性。那次是 tag 写错，改回后恢复，后来在 CI 里加了镜像 tag 校验。

## 故障二：CrashLoopBackOff

**现象：** Pod RESTARTS 不断增长，READY 在 1/1 和 0/1 之间跳。

**改什么：**

`k8s/flask-deployment.yaml`

```yaml
livenessProbe:
  httpGet:
    path: /wrong
    port: 5000
```

**执行的命令：**

```bash
vim k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期结果：**

```text
NAME                     READY   STATUS             RESTARTS   AGE
flask-xxxxx-xxxxx        1/1     Running            1          30s
flask-xxxxx-xxxxx        0/1     CrashLoopBackOff   2          60s
```

**这代表什么：** 正常应该是 `1/1 Running` 且 RESTARTS 为 0。`CrashLoopBackOff` 说明容器反复退出重启，可能应用崩了，也可能被探针杀了。需要看日志和 Events 区分。

**排查命令：**

```bash
kubectl describe pod <新flask-pod> | grep -A5 Liveness
kubectl describe pod <新flask-pod> | tail -20
kubectl logs <新flask-pod> --previous
```

**预期排查结果：**

```text
Liveness:   http-get http://:5000/wrong delay=10s timeout=1s period=10s #success=1 #failure=3

Events:
  Type     Reason     Age                From      Message
  ----     ------     ----               ----      -------
  Warning  Unhealthy  13s (x6 over 103s) kubelet   Liveness probe failed: HTTP probe failed with statuscode: 404
  Normal   Killing    13s (x2 over 83s)  kubelet   Container flask failed liveness probe, will be restarted
```

**这代表什么：** Events 写 `Liveness probe failed: 404`，是探针杀的，不是应用崩的。正常探针路径 `/health` 应返回 200。问题出在探针路径配置错误。

**根因：** 探针路径 /wrong 在 Flask 里不存在，返回 404，kubelet 判定不健康，反复杀掉重启。

**解决：**

```bash
vim k8s/flask-deployment.yaml
# 把 path: /wrong 改回 path: /health

kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期恢复结果：**

```text
NAME                     READY   STATUS    RESTARTS   AGE
flask-xxxxx-xxxxx        1/1     Running   0          30s
```

**面试描述：** 生产遇到过 CrashLoopBackOff，先 `kubectl logs --previous` 看上次崩溃日志，确认应用有没有报错，再 `kubectl describe pod` 看 Events，区分探针失败、OOM、还是应用退出。探针失败就检查路径、端口、initialDelaySeconds，应用报错就看配置、依赖、启动参数。那次是 liveness 探针路径配错，404 导致反复重启。修复后把 initialDelaySeconds 调大，避免启动慢被误杀。

## 故障三：OOMKilled

**现象：** Pod RESTARTS 快速增加，或直接 CrashLoopBackOff。

**改什么：**

`k8s/flask-deployment.yaml`

```yaml
resources:
  requests:
    cpu: 100m
    memory: 10Mi
  limits:
    cpu: 500m
    memory: 10Mi
```

注意 requests 必须小于等于 limits，否则 API 拒绝。

**执行的命令：**

```bash
vim k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期结果：**

```text
NAME                     READY   STATUS             RESTARTS      AGE
flask-xxxxx-xxxxx        0/1     OOMKilled          0             2s
flask-xxxxx-xxxxx        0/1     CrashLoopBackOff   1 (2s ago)    4s
```

**这代表什么：** 正常应该是 `1/1 Running` 且 RESTARTS 为 0。出现 `OOMKilled` 说明容器内存超过 limits 被内核杀了。需要检查资源限制是否合理，以及应用是否内存泄漏。

**排查命令：**

```bash
kubectl describe pod <新flask-pod> | grep -A5 "Last State"
```

**预期排查结果：**

```text
Last State:     Terminated
  Reason:       OOMKilled
  Exit Code:    137
  Started:      Tue, 29 Sep 2026 11:23:54 +0800
  Finished:     Tue, 29 Sep 2026 11:23:54 +0800
```

**这代表什么：** `Reason: OOMKilled` 和 `Exit Code: 137`（128+9 SIGKILL）直接说明是内存超限被杀。正常不应有 Last State Terminated。问题是 limits.memory 设太小。

**根因：** Flask 加 Python 解释器加依赖库启动需要几十 Mi，limits 只给 10Mi，内存超限被内核 OOM Killer 杀掉。反复重启。

**解决：**

```bash
vim k8s/flask-deployment.yaml
# 改回：
# requests.memory: 128Mi
# limits.memory: 256Mi

kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期恢复结果：**

```text
NAME                     READY   STATUS    RESTARTS   AGE
flask-xxxxx-xxxxx        1/1     Running   0          30s
```

**面试描述：** 生产遇到过 OOMKilled，先 `kubectl describe pod` 看 Last State，确认 Reason: OOMKilled，Exit Code: 137。137 等于 128 加 9，SIGKILL，是内核杀的。然后检查 resources，limits 是不是设太小，看监控内存趋势判断是不是内存泄漏。那次是 limits 设成 10Mi，Flask 一启动就超。修复后接入 Prometheus 内存告警，CI 里加资源校验。requests 和 limits 的关系是 requests 是调度依据，limits 是运行时上限，同一个资源 requests 必须小于等于 limits。

## 故障四：Service 不通

**现象：** Service 存在但访问不通，curl 返回 503 或超时。

**改什么：**

`k8s/flask-service.yaml`

```yaml
selector:
  app: wrong
```

**执行的命令：**

```bash
vim k8s/flask-service.yaml
kubectl apply -f k8s/flask-service.yaml
kubectl get endpoints flask -n sre-project
```

**预期结果：**

```text
NAME    ENDPOINTS   AGE
flask   <none>      30m
```

**这代表什么：** 正常应该 ENDPOINTS 列出两个 Pod IP:端口。出现 `<none>` 说明 Service 找不到后端 Pod，流量进不来。需要检查 selector 和 Pod label 是否匹配。

**排查命令：**

```bash
kubectl get endpoints flask -n sre-project
kubectl describe svc flask -n sre-project
kubectl get pods --show-labels
```

**预期排查结果：**

```text
Service 的 Selector: app=wrong
Pod 的 Labels:       app=flask
endpoints:           <none>
```

**这代表什么：** Service selector 是 `app=wrong`，Pod label 是 `app=flask`，两者不匹配，Endpoints 为空。正常应该 selector 与 Pod label 一致，Endpoints 自动填充。

**根因：** Service 的 selector 和 Pod 的 label 不匹配，Endpoints 为空，没有后端，流量进不来。

**解决：**

```bash
vim k8s/flask-service.yaml
# 把 app: wrong 改回 app: flask

kubectl apply -f k8s/flask-service.yaml
kubectl get endpoints flask -n sre-project
```

**预期恢复结果：**

```text
NAME    ENDPOINTS                               AGE
flask   10.244.58.205:5000,10.244.85.222:5000   30m
```

**面试描述：** 生产遇到过 Service 不通，先 `kubectl get endpoints` 看有没有后端。Endpoints 为空说明 selector 不匹配或 Pod 没 Ready。然后 `kubectl describe svc` 看 selector，`kubectl get pods --show-labels` 看 Pod label，对比。如果 selector 匹配但 Endpoints 还是空，检查 readinessProbe 是否通过。那次是 selector 写错，改回后 Endpoints 自动恢复。

## 故障五：Pending

**现象：** Pod 一直 Pending，不调度。

**改什么：**

`k8s/flask-deployment.yaml`

```yaml
resources:
  requests:
    cpu: 100
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 256Mi
```

注意 cpu: 100 表示 100 个 CPU 核心。

**执行的命令：**

```bash
vim k8s/flask-deployment.yaml
kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期结果：**

```text
NAME                     READY   STATUS    RESTARTS   AGE
flask-xxxxx-xxxxx        0/1     Pending   0          30s
```

**这代表什么：** 正常应该是 `1/1 Running` 且有 NODE 名字。`Pending` 说明调度器找不到满足条件的节点。需要看 Events 确定是资源不足、污点、亲和性、还是 PVC 未绑定。

**排查命令：**

```bash
kubectl describe pod <新flask-pod> | tail -20
```

**预期排查结果：**

```text
Events:
  Type     Reason            Age   From               Message
  ----     ------            ----  ----               -------
  Warning  FailedScheduling  30s   default-scheduler  0/3 nodes are available: 3 Insufficient cpu.
```

**这代表什么：** Events 写 `Insufficient cpu`，说明请求的 CPU 超过所有节点空闲量。正常应该 `Scheduled` 成功。`requests.cpu: 100` 表示请求 100 核心，节点没这么多，调度失败。

**根因：** requests.cpu 请求 100 个 CPU 核心，节点没有这么多，调度器找不到满足条件的节点。

**解决：**

```bash
vim k8s/flask-deployment.yaml
# 把 cpu: 100 改回 cpu: 100m

kubectl apply -f k8s/flask-deployment.yaml
kubectl get pods -w
```

**预期恢复结果：**

```text
NAME                     READY   STATUS    RESTARTS   AGE
flask-xxxxx-xxxxx        1/1     Running   0          30s
```

**面试描述：** 生产遇到过 Pod Pending，先 `kubectl describe pod` 看 Events。Insufficient cpu 或 memory 说明资源请求过大，node had taint 说明节点有污点要检查 tolerations，unbound PVC 说明 PVC 没绑定，node didn't match node selector 说明亲和性不满足。那次是 requests.cpu 写成 100，改成 100m 后正常调度。

## 恢复现场

五个故障做完后，执行：

```bash
kubectl apply -f k8s/
kubectl get pods
kubectl get pvc
kubectl get svc
kubectl get endpoints flask -n sre-project
```

**预期结果：**

```text
NAME                     READY   STATUS    RESTARTS   AGE
flask-xxxxx-xxxxx        1/1     Running   0          30s
flask-xxxxx-xxxxx        1/1     Running   0          30s
mysql-xxxxx-xxxxx        1/1     Running   0          16h
redis-xxxxx-xxxxx        1/1     Running   0          16h

NAME        STATUS   VOLUME                                     CAPACITY   ACCESS MODES
mysql-pvc   Bound    pvc-88994d94-1fa2-44bc-8cd8-e9c0aa451690   5Gi        RWO

NAME    TYPE        CLUSTER-IP    EXTERNAL-IP   PORT(S)
flask   ClusterIP   10.4.92.192   <none>        80/TCP
mysql   ClusterIP   None          <none>        3306/TCP
redis   ClusterIP   10.0.78.127   <none>        6379/TCP

NAME    ENDPOINTS                               AGE
flask   10.244.58.205:5000,10.244.85.222:5000   30m
```

**这代表什么：** 所有 Pod `1/1 Running`，PVC `Bound`，Service 和 Endpoints 正常，五个故障全部恢复，集群回到健康状态。
