
pipeline {
    agent any

    environment {
        AWS_REGION = 'ap-south-1'
        ECR_REGISTRY = '772607727551.dkr.ecr.ap-south-1.amazonaws.com'
        ECR_REPOSITORY = 'eye-tracking-mouse-cca02'
        IMAGE_NAME = 'eye-tracking-mouse-cca02'
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Python Validation') {
            steps {
                sh 'python3 -m py_compile eye.py'
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t ${IMAGE_NAME}:${BUILD_NUMBER} .'
            }
        }

        stage('Login to Amazon ECR') {
            steps {
                sh '''
                    aws sts get-caller-identity
                    aws ecr get-login-password --region "$AWS_REGION" |
                    docker login --username AWS --password-stdin "$ECR_REGISTRY"
                '''
            }
        }

        stage('Push Image to ECR') {
            steps {
                sh '''
                    docker tag "${IMAGE_NAME}:${BUILD_NUMBER}" \
                    "${ECR_REGISTRY}/${ECR_REPOSITORY}:${BUILD_NUMBER}"

                    docker push \
                    "${ECR_REGISTRY}/${ECR_REPOSITORY}:${BUILD_NUMBER}"

                    docker tag "${IMAGE_NAME}:${BUILD_NUMBER}" \
                    "${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"

                    docker push \
                    "${ECR_REGISTRY}/${ECR_REPOSITORY}:latest"
                '''
            }
        }
    }

    post {
        success {
            echo 'SUCCESS: Docker image pushed to Amazon ECR.'
        }
        failure {
            echo 'FAILED: Check the Console Output for the error.'
        }
    }
}
