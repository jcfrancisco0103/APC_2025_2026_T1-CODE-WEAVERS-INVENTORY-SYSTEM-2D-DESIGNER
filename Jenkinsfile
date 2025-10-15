pipeline {
    agent {
        docker {
            image 'python:3.9-slim'
            args '-v /var/run/docker.sock:/var/run/docker.sock'
        }
    }

    environment {
        PYTHON = 'python3'
        VENV_DIR = '.venv'
        DOCKER_COMPOSE_FILE = 'docker-compose.yml'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
                echo 'Code checked out successfully'
            }
        }

        stage('Setup Environment') {
            steps {
                sh '''
                    apt-get update
                    apt-get install -y docker.io docker-compose
                    ${PYTHON} -m venv ${VENV_DIR}
                    . ${VENV_DIR}/bin/activate
                    pip install --upgrade pip
                    pip install -r requirements.txt
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                    . ${VENV_DIR}/bin/activate
                    python manage.py test --verbosity=2
                '''
            }
        }

        stage('Build Docker Images') {
            steps {
                sh '''
                    docker-compose -f ${DOCKER_COMPOSE_FILE} build
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    docker-compose -f ${DOCKER_COMPOSE_FILE} down
                    docker-compose -f ${DOCKER_COMPOSE_FILE} up -d web db
                '''
            }
        }

        stage('Health Check') {
            steps {
                sh '''
                    sleep 30
                    curl -f http://localhost:8000 || exit 1
                '''
            }
        }
    }

    post {
        always {
            echo 'Pipeline execution completed.'
            sh 'docker-compose -f ${DOCKER_COMPOSE_FILE} logs'
        }
        success {
            echo 'Pipeline executed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check logs for details.'
            sh 'docker-compose -f ${DOCKER_COMPOSE_FILE} down'
        }
        cleanup {
            sh 'docker system prune -f'
        }
    }
}
