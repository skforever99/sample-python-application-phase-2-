pipeline {
    agent any

    environment {
        DOCKERHUB_USERNAME = 'skforever99'
        IMAGE_NAME          = "${DOCKERHUB_USERNAME}/sample-python-app"
        IMAGE_TAG           = "${env.BUILD_NUMBER}"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${IMAGE_NAME}:${IMAGE_TAG} -t ${IMAGE_NAME}:latest ."
            }
        }

        stage('Push to Docker Hub') {
            steps {
                withCredentials([usernamePassword(
                    credentialsId: 'dockerhub-creds',
                    usernameVariable: 'DOCKER_USER',
                    passwordVariable: 'DOCKER_PASS'
                )]) {
                    sh 'echo "$DOCKER_PASS" | docker login -u "$DOCKER_USER" --password-stdin'
                    sh "docker push ${IMAGE_NAME}:${IMAGE_TAG}"
                    sh "docker push ${IMAGE_NAME}:latest"
                }
            }
        }

        stage('Deploy to k3s') {
            steps {
                withCredentials([file(credentialsId: 'k3s-kubeconfig', variable: 'KUBECONFIG_FILE')]) {
                    sh """
                        export KUBECONFIG=\$KUBECONFIG_FILE
                        sed -e 's|skforever99|${DOCKERHUB_USERNAME}|' \
                            -e 's|IMAGE_TAG_PLACEHOLDER|${IMAGE_TAG}|' \
                            deployment.yaml > deployment.rendered.yaml

                        sh 'curl -k -m 5 https://172.31.33.39:6443 || echo CURL_FAILED'
                        kubectl apply -f service.yaml --validate=false
                        kubectl apply -f deployment.rendered.yaml --validate=false
                        kubectl rollout status deployment/sample-python-app --timeout=90s
                    """
                }
            }
        }
    }

    post {
        success {
            echo "Deployed ${IMAGE_NAME}:${IMAGE_TAG}. App reachable at http://<k3s_node_ip>:30080"
        }
    }
}
