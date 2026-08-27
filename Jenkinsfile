pipeline {
    agent any

    environment {
        IMAGE_NAME = 'integrator-inventory'
        CONTAINER_NAME = 'integrator-inventory'
    }

    stages {

        stage('Checkout') {
            steps {
                echo 'Retrieving Inventory Management System from GitHub...'
                checkout scm
            }
        }

        stage('Validate') {
            steps {
                echo 'Validating project structure...'
                sh '''
                    test -f app.py
                    test -f requirements.txt
                    test -f Dockerfile
                    test -f Jenkinsfile
                    test -f tests/test_app.py
                '''
            }
        }

        stage('Application Test') {
            steps {
                echo 'Running application syntax validation...'
                sh '''
                    python3 -m py_compile app.py
                '''
            }
        }

        stage('Docker Build') {
            steps {
                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                }

                echo "Building Docker image ${IMAGE_NAME}:${IMAGE_TAG}"

                sh '''
                    docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .
                '''
            }
        }

        stage('Deploy') {
            steps {
                echo 'Deploying Inventory Management System...'

                sh '''
                    docker rm -f ${CONTAINER_NAME} 2>/dev/null || true

                    docker run -d \
                      --name ${CONTAINER_NAME} \
                      -p 5000:5000 \
                      --restart unless-stopped \
                      -e SECRET_KEY=jenkins-demo-secret \
                      -e ADMIN_EMAIL=admin@integratortool.com \
                      -e ADMIN_PASSWORD=Admin@123 \
                      ${IMAGE_NAME}:${IMAGE_TAG}
                '''
            }
        }

        stage('Deployment Verification') {
            steps {
                echo 'Verifying deployed application...'

                sh '''
                    sleep 10
                    docker ps --filter name=${CONTAINER_NAME}
                    curl -fsS http://127.0.0.1:5000/api/health
                '''
            }
        }
    }

    post {
        success {
            echo 'Inventory Management System CI/CD pipeline completed successfully.'
        }

        failure {
            echo 'Inventory Management System CI/CD pipeline failed. Review the failed stage and console output.'
        }

        always {
            echo 'Pipeline execution completed.'
        }
    }
}
