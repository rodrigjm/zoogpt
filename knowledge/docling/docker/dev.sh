#!/bin/bash
# Development helper script for Docker Compose

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$SCRIPT_DIR/docker-compose.dev.yml"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"

    if ! command_exists docker; then
        echo -e "${RED}Error: docker is not installed${NC}"
        exit 1
    fi

    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        echo -e "${RED}Error: docker-compose is not installed${NC}"
        exit 1
    fi

    if [ ! -f "$SCRIPT_DIR/.env" ]; then
        echo -e "${YELLOW}Warning: .env file not found. Creating from .env.example${NC}"
        cp "$SCRIPT_DIR/.env.example" "$SCRIPT_DIR/.env"
        echo -e "${RED}Please edit docker/.env and add your OPENAI_API_KEY${NC}"
        exit 1
    fi

    if [ ! -d "$PROJECT_ROOT/data" ]; then
        echo -e "${YELLOW}Warning: data directory not found. Creating...${NC}"
        mkdir -p "$PROJECT_ROOT/data"
    fi

    echo -e "${GREEN}Requirements check passed${NC}"
}

start() {
    check_requirements
    echo -e "${GREEN}Starting development environment...${NC}"
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose.dev.yml up --build
}

start_detached() {
    check_requirements
    echo -e "${GREEN}Starting development environment in background...${NC}"
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose.dev.yml up -d --build
    echo -e "${GREEN}Services started. Use 'docker compose -f docker/docker-compose.dev.yml logs -f' to view logs${NC}"
}

stop() {
    echo -e "${YELLOW}Stopping development environment...${NC}"
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose.dev.yml down
    echo -e "${GREEN}Services stopped${NC}"
}

restart() {
    stop
    start_detached
}

logs() {
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose.dev.yml logs -f "$@"
}

status() {
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}Service Status:${NC}"
    docker compose -f docker-compose.dev.yml ps
    echo ""
    echo -e "${GREEN}Health Check:${NC}"
    curl -s http://localhost:8000/health || echo -e "${RED}API health check failed${NC}"
}

clean() {
    echo -e "${YELLOW}Stopping and removing containers, networks, and volumes...${NC}"
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose.dev.yml down -v
    echo -e "${GREEN}Cleanup complete${NC}"
}

rebuild() {
    echo -e "${YELLOW}Rebuilding containers...${NC}"
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose.dev.yml build --no-cache
    echo -e "${GREEN}Rebuild complete${NC}"
}

shell() {
    local service="${1:-api}"
    cd "$SCRIPT_DIR"
    docker compose -f docker-compose.dev.yml exec "$service" /bin/bash
}

usage() {
    echo "Zoocari Development Environment Helper"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start       Start services in foreground (default)"
    echo "  up          Start services in background"
    echo "  stop        Stop services"
    echo "  restart     Restart services"
    echo "  logs [svc]  Follow logs (optionally specify service: api, web)"
    echo "  status      Show service status and health"
    echo "  clean       Stop and remove containers, networks, volumes"
    echo "  rebuild     Rebuild containers from scratch"
    echo "  shell [svc] Open shell in service container (default: api)"
    echo ""
    echo "Examples:"
    echo "  $0 start                # Start in foreground"
    echo "  $0 up                   # Start in background"
    echo "  $0 logs api             # Follow API logs"
    echo "  $0 shell web            # Open shell in web container"
}

# Main command router
case "${1:-start}" in
    start)
        start
        ;;
    up)
        start_detached
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    logs)
        shift
        logs "$@"
        ;;
    status)
        status
        ;;
    clean)
        clean
        ;;
    rebuild)
        rebuild
        ;;
    shell)
        shift
        shell "$@"
        ;;
    help|--help|-h)
        usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        usage
        exit 1
        ;;
esac
