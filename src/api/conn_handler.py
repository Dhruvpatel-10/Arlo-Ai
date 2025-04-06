import subprocess
import time
from src.utils.logger import setup_logging

class FastAPIServer:
    def __init__(self, module_name="src.api.main", host="0.0.0.0", port=8000):
        self.logger = setup_logging(module_name="FastAPIServer")
        self.module_name = module_name
        self.host = host
        self.port = port
        self.process = None

    def start(self):
        """Starts FastAPI as a subprocess."""
        if self.process is None:
            # Use --reload for development to catch changes
            self.process = subprocess.Popen(
                ["uvicorn", f"{self.module_name}:app", "--host", self.host, "--port", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            self.logger.info(f"✅ FastAPI started on {self.host}:{self.port} (PID: {self.process.pid})")
            
            # Add a brief check to see if server actually started properly
            time.sleep(1)
            if self.process.poll() is not None:
                stderr = self.process.stderr.read().decode()
                self.logger.error(f"Server failed to start: {stderr}")
                return False
            return True
        return False


    # Add to FastAPIServer
    def stop(self):
        """Performs a more graceful shutdown with proper signal handling"""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait()
            self.logger.warning("❌ FastAPI stopped.")
            self.process = None

# ✅ Example usage:
if __name__ == "__main__":
    server = FastAPIServer()
    
    server.start()
    time.sleep(10)  # Simulate work while FastAPI is running
    
    server.stop()
