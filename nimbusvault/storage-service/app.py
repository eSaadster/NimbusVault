from shared.logger import configure_logger

logger = configure_logger("storage-service")

if __name__ == "__main__":
    logger.info("Storage service started")
