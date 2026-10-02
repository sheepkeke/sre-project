# Runbook

## Pod 崩溃
1. kubectl get pods -n sre-project
2. kubectl describe pod <pod> -n sre-project
3. kubectl logs <pod> -n sre-project --previous
4. 根据 Events 判断：镜像问题、探针问题、OOM、资源不足
5. 修复后 kubectl apply

## MySQL 慢查询
1. kubectl exec -it <mysql-pod> -n sre-project -- mysql -uroot -proot123
2. SHOW PROCESSLIST;
3. SHOW ENGINE INNODB STATUS;
4. 分析慢查询日志，加索引或优化 SQL

## 磁盘满
1. df -h
2. du -sh /var/lib/docker/*
3. 清理旧镜像：docker image prune -a
4. 清理日志：find /var/log -name "*.log" -mtime +7 -delete

## 服务 502
1. kubectl get endpoints flask -n sre-project
2. 如果 Endpoints 为空，检查 selector 和 Pod label
3. kubectl get pods -n sre-project
4. 如果 Pod 没 Ready，检查 readinessProbe
5. kubectl logs <pod> -n sre-project

## 节点 NotReady
1. kubectl get nodes
2. kubectl describe node <node>
3. 检查 kubelet：systemctl status kubelet
4. 检查磁盘、内存、网络
5. 恢复后节点自动 Ready
