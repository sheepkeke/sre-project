pipeline {
    agent any

    environment {
        HARBOR = '192.168.37.10:8080'
        PROJECT = 'sre-project'
        IMAGE = "${HARBOR}/${PROJECT}/sre-flask"
        TAG = "${BUILD_NUMBER}"
    }

    stages {
        stage('拉代码') {
            steps {
                git branch: 'main', url: 'https://github.com/sheepkeke/sre-project.git'
            }
        }

        stage('构建镜像') {
            steps {
                sh 'docker build -t ${IMAGE}:${TAG} .'
                sh 'docker tag ${IMAGE}:${TAG} ${IMAGE}:latest'
            }
        }

        stage('推送 Harbor') {
            steps {
                sh 'docker login ${HARBOR} -u admin -p Harbor12345'
                sh 'docker push ${IMAGE}:${TAG}'
                sh 'docker push ${IMAGE}:latest'
            }
        }

        stage('部署到 K8s') {
            steps {
                sh 'kubectl set image deployment/flask flask=${IMAGE}:${TAG} -n sre-project'
                sh 'kubectl rollout status deployment/flask -n sre-project'
            }
        }

        stage('验证') {
            steps {
                sh 'kubectl get pods -n sre-project'
            }
        }
    }

    post {
        success {
            echo '部署成功'
        }
        failure {
            echo '部署失败'
        }
    }
}
