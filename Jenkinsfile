pipeline {
    agent any

    environment {
        IMAGE_NAME = 'django-k8s'
        IMAGE_TAG = "${BUILD_NUMBER}"
        REGISTRY = 'yourdockerhubuser'
        FULL_IMAGE = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"
        K8S_DIR = "${WORKSPACE}/k8s"
        APP_DIR = "${WORKSPACE}/app"
        KUBECONFIG = credentials('kubeconfig')  // EC2 cluster kubeconfig (secret file)
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${FULL_IMAGE} ${APP_DIR}'
                sh 'docker tag ${FULL_IMAGE} ${REGISTRY}/${IMAGE_NAME}:latest'
            }
        }

        stage('Push Image to Registry') {
            steps {
                withDockerRegistry(credentialsId: 'docker-hub-credentials', url: '') {
                    sh 'docker push ${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}'
                    sh 'docker push ${REGISTRY}/${IMAGE_NAME}:latest'
                }
            }
        }

        stage('Update Kubeconfig') {
            steps {
                script {
                    sh 'mkdir -p $HOME/.kube'
                    sh 'cp ${KUBECONFIG} $HOME/.kube/config'
                    sh 'kubectl config current-context'
                }
            }
        }

        stage('Deploy to Kubernetes') {
            steps {
                sh 'kubectl apply -f ${K8S_DIR}/configmap.yaml'
                sh 'kubectl apply -f ${K8S_DIR}/postgres.yaml'
                sh 'kubectl wait --for=condition=ready pod -l app=postgres --timeout=120s'
                sh "sed -i 's|image: django-k8s:latest|image: ${FULL_IMAGE}|g' ${K8S_DIR}/django.yaml"
                sh 'kubectl apply -f ${K8S_DIR}/django.yaml'
                sh 'kubectl rollout status deployment/django --timeout=180s'
            }
        }

        stage('Run Migrations') {
            steps {
                sh 'kubectl exec deploy/django -- python manage.py migrate --noinput'
            }
        }

        stage('Verify Deployment') {
            steps {
                sh 'kubectl get pods -o wide'
                sh 'kubectl get svc django'
            }
        }
    }

    post {
        success {
            echo 'Deployment successful! Access at http://<EC2_PUBLIC_IP>:8000/'
            sh 'kubectl get pods -l app=django'
        }
        failure {
            echo 'Deployment failed. Check logs:'
            sh 'kubectl logs deployment/django --tail=50 || true'
            sh 'kubectl get pods -o wide'
        }
    }
}
