#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# --- Configuration ---
HARBOR_REGISTRY="harbor.my-basement.cloud"
HARBOR_PROJECT="subsy"
IMAGE_NAME="glitch-hunt-api"
NAMESPACE="glitch-hunt"
CHART_PATH="./k8s/charts/glitch-hunt"
RELEASE_NAME="glitch-hunt"

# --- Credentials ---
# Using the credentials provided. 
# NOTE: Ensure this robot account has push permissions to the 'glitch-hunt' project in Harbor.
HARBOR_ROBOT_USER="robot\$subsy-builder"
HARBOR_ROBOT_SECRET="fsvMCZvTB9tNIRJSzzm7rwdSF38aRHsZ"

# --- Helper Functions ---

print_usage() {
    echo "Usage: ./deploy.sh [COMMAND] [TAG]"
    echo ""
    echo "Commands:"
    echo "  all    📦 + 🚀  Build, Push, Helm Upgrade, and Rollout (Default)"
    echo "  build  📦       Only Build and Push Docker Image"
    echo "  helm   🚀       Only Helm Upgrade"
    echo ""
    echo "Arguments:"
    echo "  TAG    Optional. Image tag to use (default: 'dev-latest' for non-prod)"
    echo ""
    echo "Examples:"
    echo "  ./deploy.sh all v1.0.0"
    echo "  ./deploy.sh build"
}

docker_login() {
    echo "🔐 Logging into Harbor ($HARBOR_REGISTRY)..."
    echo "$HARBOR_ROBOT_SECRET" | docker login "$HARBOR_REGISTRY" -u "$HARBOR_ROBOT_USER" --password-stdin
}

build_and_push() {
    local TAG=$1
    local FULL_IMAGE="$HARBOR_REGISTRY/$HARBOR_PROJECT/$IMAGE_NAME:$TAG"

    echo "🏗️  Building and Pushing image: $FULL_IMAGE"
    
    # Ensure buildx is ready
    # docker buildx create --use || true 

    docker buildx build \
        --platform linux/amd64 \
        -t "$FULL_IMAGE" \
        --push \
        .
    
    echo "✅ Build and Push complete!"
}

helm_upgrade() {
    local TAG=$1
    local FULL_REPO="$HARBOR_REGISTRY/$HARBOR_PROJECT/$IMAGE_NAME"

    echo "☸️  Deploying to Kubernetes (Namespace: $NAMESPACE)..."

    # Ensure namespace exists
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # Helm Upgrade with forced image update
    helm upgrade --install "$RELEASE_NAME" "$CHART_PATH" \
        --namespace "$NAMESPACE" \
        --set api.image.repository="$FULL_REPO" \
        --set api.image.tag="$TAG" \
        --wait

    echo "✅ Helm release updated."
}

rollout_restart() {
    echo "vk  Triggering Rollout Restart..."
    kubectl rollout restart deployment/"$RELEASE_NAME"-api -n "$NAMESPACE"
    echo "✅ Rollout triggered."
}

# --- Main Logic ---

COMMAND=$1
TAG=${2:-"dev-latest"}

if [[ -z "$COMMAND" ]]; then
    print_usage
    exit 1
fi

case "$COMMAND" in
    all) 
        echo "🚀 Starting Full Deployment (Tag: $TAG)..."
        docker_login
        build_and_push "$TAG"
        helm_upgrade "$TAG"
        rollout_restart
        echo "🎉 Deployment Complete!"
        ;;
    build) 
        echo "📦 Starting Build & Push Only (Tag: $TAG)..."
        docker_login
        build_and_push "$TAG"
        echo "🎉 Build Complete!"
        ;;
    helm) 
        echo "🚀 Starting Helm Upgrade Only (Tag: $TAG)..."
        helm_upgrade "$TAG"
        echo "🎉 Upgrade Complete!"
        ;;
    *)
        echo "❌ Invalid Command: $COMMAND"
        print_usage
        exit 1
        ;;
esac
