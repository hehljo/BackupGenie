#!/bin/bash
################################################################################
# BackupGenie - Universal Installation Script
# One-command setup for all platforms
################################################################################

set -e

# Configuration
REPO_URL="${REPO_URL:-https://github.com/hehljo/BackupGenie.git}"
BRANCH="${BRANCH:-main}"
INSTALL_DIR="${INSTALL_DIR:-/opt/BackupGenie}"
TEMP_DIR=$(mktemp -d)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print banner
echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   BackupGenie Installer                   ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}\n"

# Function to check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        echo -e "${YELLOW}⚠ Running as root. This is OK but not required.${NC}\n"
    fi
}

# Function to detect platform
detect_platform() {
    if grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
        echo "raspberry-pi"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    else
        echo "unknown"
    fi
}

# Function to check prerequisites
check_prerequisites() {
    local missing_deps=()

    # Check for essential tools
    for cmd in curl git; do
        if ! command -v "$cmd" &> /dev/null; then
            missing_deps+=("$cmd")
        fi
    done

    if [ ${#missing_deps[@]} -ne 0 ]; then
        echo -e "${RED}✗ Missing required dependencies: ${missing_deps[*]}${NC}"
        echo -e "${YELLOW}Installing missing dependencies...${NC}"

        if command -v apt &> /dev/null; then
            sudo apt update
            sudo apt install -y "${missing_deps[@]}"
        elif command -v yum &> /dev/null; then
            sudo yum install -y "${missing_deps[@]}"
        else
            echo -e "${RED}Error: Unable to install dependencies automatically.${NC}"
            echo "Please install: ${missing_deps[*]}"
            exit 1
        fi
    fi
}

# Main installation
main() {
    check_root
    check_prerequisites

    local platform=$(detect_platform)
    echo -e "${GREEN}✓ Detected platform: $platform${NC}\n"

    # Clone repository to temporary directory
    echo -e "${YELLOW}Downloading BackupGenie...${NC}"
    cd "$TEMP_DIR"
    git clone -b "$BRANCH" "$REPO_URL" backupgenie 2>/dev/null || {
        echo -e "${RED}Failed to clone repository${NC}"
        echo "Repository: $REPO_URL"
        echo "Branch: $BRANCH"
        exit 1
    }
    cd backupgenie

    echo -e "${GREEN}✓ Repository downloaded${NC}\n"

    # Choose installation method based on platform and user preference
    echo "Select installation method:"
    echo "  1) Quick Deploy (Recommended - Full automated setup)"
    echo "  2) Raspberry Pi Setup (Interactive setup for RPi)"
    echo "  3) Setup Wizard (Step-by-step configuration)"
    echo "  4) Manual (Just clone repository, configure yourself)"
    echo ""

    # Auto-select for non-interactive mode (when piped)
    if [ -t 0 ]; then
        read -p "Enter choice [1-4] (default: 1): " choice
        choice=${choice:-1}
    else
        echo "Non-interactive mode detected, using Quick Deploy..."
        choice=1
    fi

    case $choice in
        1)
            echo -e "\n${BLUE}Starting Quick Deploy...${NC}\n"
            bash scripts/quick-deploy.sh
            ;;
        2)
            if [ "$platform" != "raspberry-pi" ]; then
                echo -e "${YELLOW}⚠ Warning: This doesn't appear to be a Raspberry Pi${NC}"
                read -p "Continue anyway? (y/N) " -n 1 -r
                echo
                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    exit 1
                fi
            fi
            echo -e "\n${BLUE}Starting Raspberry Pi Setup...${NC}\n"
            bash scripts/setup-raspberry-pi.sh
            ;;
        3)
            echo -e "\n${BLUE}Starting Setup Wizard...${NC}\n"
            bash scripts/setup-wizard.sh
            ;;
        4)
            echo -e "\n${BLUE}Manual Installation${NC}\n"
            if [ ! -d "$INSTALL_DIR" ]; then
                sudo mkdir -p "$INSTALL_DIR"
                sudo chown ${SUDO_USER:-$USER}:${SUDO_USER:-$USER} "$INSTALL_DIR"
            fi
            cp -r . "$INSTALL_DIR/"
            cd "$INSTALL_DIR"
            echo -e "${GREEN}✓ Repository cloned to $INSTALL_DIR${NC}"
            echo ""
            echo "Next steps:"
            echo "  1. cd $INSTALL_DIR"
            echo "  2. cp .env.example .env"
            echo "  3. nano .env"
            echo "  4. docker compose up -d"
            echo ""
            ;;
        *)
            echo -e "${RED}Invalid choice${NC}"
            exit 1
            ;;
    esac

    # Cleanup
    cd /
    rm -rf "$TEMP_DIR"
}

# Run main function
main "$@"
