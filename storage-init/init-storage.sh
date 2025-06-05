#!/bin/bash
set -e

# Root directory for all vault storage
VAULT_ROOT="/vault-storage"

echo "Initializing storage structure at $VAULT_ROOT ..."

# Create NextCloud-compatible structure
mkdir -p \
  "$VAULT_ROOT"/files \      # Main file storage
  "$VAULT_ROOT"/users/admin \ # Admin user directory
  "$VAULT_ROOT"/users/user1 \ # Example user directories
  "$VAULT_ROOT"/users/user2 \
  "$VAULT_ROOT"/shared \     # Public/shared files
  "$VAULT_ROOT"/trash \      # Recycle bin
  "$VAULT_ROOT"/external \   # External storage mounts
  "$VAULT_ROOT"/uploads \    # Temporary upload staging
  "$VAULT_ROOT"/temp \       # Processing temporary files
  "$VAULT_ROOT"/versions \   # File version history
  "$VAULT_ROOT"/config       # System configuration

# Link external storage to NimbusVault files
ln -sfn "$VAULT_ROOT"/files "$VAULT_ROOT"/external/nimbusvault

# Set permissions so all services can read the directories
chmod -R 755 "$VAULT_ROOT"

echo "Storage structure initialized!"
