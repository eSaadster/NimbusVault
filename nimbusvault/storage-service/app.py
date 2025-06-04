import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "common"))
from storage_utils import save_file

print("Hello from storage-service")
save_file("storage.txt", "storage-service")
