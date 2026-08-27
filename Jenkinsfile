pipeline {
  agent any
  environment { IMAGE_NAME = "integrator-inventory"; IMAGE_TAG = "${env.GIT_COMMIT?.take(7) ?: env.BUILD_NUMBER}"; CONTAINER = "integrator-inventory" }
  stages {
    stage('Checkout') { steps { checkout scm } }
    stage('Validate') { steps { sh 'test -f app.py'; sh 'test -f Dockerfile'; sh 'python3 -m py_compile app.py' } }
    stage('Test') { steps { sh '''python3 -m venv .venv
. .venv/bin/activate
pip install -q -r requirements.txt
pytest -q''' } }
    stage('Docker Build') { steps { sh 'docker build -t ${IMAGE_NAME}:${IMAGE_TAG} .' } }
    stage('Deploy') { steps { sh '''docker rm -f ${CONTAINER} 2>/dev/null || true
docker run -d --name ${CONTAINER} -p 5000:5000 --restart unless-stopped -e SECRET_KEY=jenkins-demo-secret -e ADMIN_EMAIL=admin@integratortool.com -e ADMIN_PASSWORD=Admin@123 ${IMAGE_NAME}:${IMAGE_TAG}''' } }
    stage('Verify') { steps { sh '''sleep 8
curl -fsS http://127.0.0.1:5000/api/health
docker ps --filter name=${CONTAINER}''' } }
  }
  post { success { echo "Inventory CI/CD completed successfully: ${IMAGE_NAME}:${IMAGE_TAG}" } failure { echo "Pipeline failed. Review console output." } }
}
