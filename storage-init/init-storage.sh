#!/bin/bash
set -e

# Root directory for all vault storage
VAULT_ROOT="/vault-storage"

echo "Initializing storage structure at $VAULT_ROOT ..."

# Create NextCloud-compatible structure
mkdir -p \ 
  "$VAULT_ROOT"/uploads \    # Temporary upload staging
  "$VAULT_ROOT"/files \      # Permanent file storage
  "$VAULT_ROOT"/users \      # User-specific directories
  "$VAULT_ROOT"/shared \     # Shared/public files
  "$VAULT_ROOT"/trash \      # Deleted files retention
  "$VAULT_ROOT"/temp \       # Processing temporary files
  "$VAULT_ROOT"/versions \   # File version history
  "$VAULT_ROOT"/config       # System configuration

# Set permissions so all services can read the directories
chmod -R 755 "$VAULT_ROOT"

echo "Storage structure initialized!"
