pipeline {
    agent any

    environment {
        // Docker Hub / Registry Configurations
        IMAGE_NAME = 'django-k8s'
        IMAGE_TAG = "${BUILD_NUMBER}"
        REGISTRY = 'ayushyash71' // <-- Yaha apna Docker Hub username dalein
        FULL_IMAGE = "${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

        // Kubernetes Configurations
        K8S_NAMESPACE = 'django-project'
        K8S_DIR = "${WORKSPACE}/k8s"
        APP_DIR = "${WORKSPACE}" // Root folder workspace

        // Kubeconfig Path (Jenkins user context)
        KUBECONFIG = '/var/lib/jenkins/.kube/config'
    }

    stages {

        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Verify Environment') {
            steps {
                sh '''
                    echo "Checking Docker..."
                    docker --version

                    echo "Checking kubectl..."
                    kubectl version --client

                    echo "Checking Kubernetes & Nodes..."
                    kubectl get nodes --kubeconfig=${KUBECONFIG} || kubectl get nodes

                    echo "Checking kubeconfig context..."
                    kubectl config current-context --kubeconfig=${KUBECONFIG} || true
                '''
            }
        }

        stage('Build Docker Image') {
            steps {
                sh '''
                    echo "Building Docker Image..."
                    docker build \
                      -t ${FULL_IMAGE} \
                      -t ${REGISTRY}/${IMAGE_NAME}:latest \
                      ${APP_DIR}
                '''
            }
        }

        stage('Create Namespace') {
            steps {
                sh '''
                    kubectl create namespace ${K8S_NAMESPACE} \
                      --dry-run=client \
                      -o yaml | kubectl apply --kubeconfig=${KUBECONFIG} -f -
                '''
            }
        }

        stage('Push Image to Registry') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'docker-hub-credentials',
                        usernameVariable: 'DOCKER_USERNAME',
                        passwordVariable: 'DOCKER_PASSWORD'
                    )
                ]) {
                    sh '''
                        echo "$DOCKER_PASSWORD" | docker login \
                            -u "$DOCKER_USERNAME" \
                            --password-stdin

                        docker push ${FULL_IMAGE}
                        docker push ${REGISTRY}/${IMAGE_NAME}:latest

                        docker logout
                    '''
                }
            }
        }

        stage('Deploy PostgreSQL') {
            steps {
                sh '''
                    if [ -f "${K8S_DIR}/configmap.yaml" ]; then
                        kubectl apply -f ${K8S_DIR}/configmap.yaml -n ${K8S_NAMESPACE} --kubeconfig=${KUBECONFIG}
                    fi

                    if [ -f "${K8S_DIR}/postgres.yaml" ]; then
                        kubectl apply -f ${K8S_DIR}/postgres.yaml -n ${K8S_NAMESPACE} --kubeconfig=${KUBECONFIG}
                        
                        echo "Waiting for PostgreSQL..."
                        kubectl wait \
                          --for=condition=ready \
                          pod \
                          -l app=postgres \
                          -n ${K8S_NAMESPACE} \
                          --timeout=180s --kubeconfig=${KUBECONFIG} || echo "Postgres pod wait skipped or timeout"
                    fi
                '''
            }
        }

        stage('Deploy Django') {
            steps {
                sh '''
                    # Django deployment manifest me latest image tag replace karein
                    sed -i "s|image: .*|image: ${FULL_IMAGE}|g" ${K8S_DIR}/django.yaml

                    kubectl apply \
                      -f ${K8S_DIR}/django.yaml \
                      -n ${K8S_NAMESPACE} \
                      --kubeconfig=${KUBECONFIG}

                    echo "Waiting for Django deployment..."
                    kubectl rollout status \
                      deployment/django \
                      -n ${K8S_NAMESPACE} \
                      --timeout=180s \
                      --kubeconfig=${KUBECONFIG}
                '''
            }
        }

        stage('Run Migrations') {
            steps {
                sh '''
                    echo "Running database migrations..."
                    kubectl exec \
                      -n ${K8S_NAMESPACE} \
                      deployment/django \
                      --kubeconfig=${KUBECONFIG} \
                      -- python manage.py migrate --noinput || echo "Migrations command exited or not configured"
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    echo "===== PODS ====="
                    kubectl get pods -n ${K8S_NAMESPACE} -o wide --kubeconfig=${KUBECONFIG}

                    echo "===== SERVICES ====="
                    kubectl get svc -n ${K8S_NAMESPACE} --kubeconfig=${KUBECONFIG}

                    echo "===== DEPLOYMENTS ====="
                    kubectl get deployments -n ${K8S_NAMESPACE} --kubeconfig=${KUBECONFIG}
                '''
            }
        }
    }

    post {
        success {
            echo 'Deployment successful! Django application deployed to Minikube cluster.'
            sh '''
                kubectl get pods,svc -n ${K8S_NAMESPACE} --kubeconfig=${KUBECONFIG}
            '''
        }

        failure {
            echo 'Deployment failed. Fetching Kubernetes status & logs...'
            sh '''
                echo "===== PODS STATUS ====="
                kubectl get pods -n ${K8S_NAMESPACE} -o wide --kubeconfig=${KUBECONFIG} || true

                echo "===== RECENT EVENTS ====="
                kubectl get events -n ${K8S_NAMESPACE} --sort-by='.metadata.creationTimestamp' --kubeconfig=${KUBECONFIG} || true

                echo "===== DJANGO LOGS ====="
                kubectl logs deployment/django -n ${K8S_NAMESPACE} --tail=50 --kubeconfig=${KUBECONFIG} || true

                echo "===== POSTGRES LOGS ====="
                kubectl logs deployment/postgres -n ${K8S_NAMESPACE} --tail=50 --kubeconfig=${KUBECONFIG} || true
            '''
        }
    }
}
