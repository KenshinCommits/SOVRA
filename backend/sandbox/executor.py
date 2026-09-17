import docker
import os
import uuid
import time
from typing import Dict, Any

# Ensure absolute paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ARTIFACTS_DIR = os.path.join(BASE_DIR, "backend", "artifacts")
SANDBOX_TMP_DIR = os.path.join(ARTIFACTS_DIR, "sandbox_tmp")

os.makedirs(SANDBOX_TMP_DIR, exist_ok=True)

class SandboxExecutor:
    def __init__(self, image: str = "python:3.12-alpine", max_execution_time: int = 10):
        self.image = image
        self.max_execution_time = max_execution_time
        self._client = None

    @property
    def client(self):
        if self._client is None:
            try:
                self._client = docker.from_env()
            except Exception as e:
                raise RuntimeError(f"Could not connect to Docker daemon: {e}")
        return self._client

    def execute(self, code: str) -> Dict[str, Any]:
        """
        Executes Python code in an isolated Docker sandbox.
        """
        execution_id = str(uuid.uuid4())
        script_filename = f"script_{execution_id}.py"
        script_path = os.path.join(SANDBOX_TMP_DIR, script_filename)

        # Write the code to a temporary file in the sandbox directory
        with open(script_path, "w") as f:
            f.write(code)

        container = None
        start_time = time.time()
        
        try:
            # Create and start the container
            # Restrictions: network_mode="none", mem_limit="128m", mount only the script
            container = self.client.containers.run(
                image=self.image,
                command=["python", f"/sandbox/{script_filename}"],
                volumes={
                    SANDBOX_TMP_DIR: {'bind': '/sandbox', 'mode': 'ro'}
                },
                working_dir="/sandbox",
                network_mode="none",
                mem_limit="128m",
                detach=True,
                remove=False
            )
            
            # Wait for completion or timeout
            result = container.wait(timeout=self.max_execution_time)
            exit_code = result.get("StatusCode", -1)
            
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')
            
            end_time = time.time()
            return {
                "exit_code": exit_code,
                "output": logs.strip(),
                "execution_time_seconds": round(end_time - start_time, 2),
                "status": "success" if exit_code == 0 else "error"
            }
            
        except Exception as e:
            import requests
            # Catch docker errors and timeouts
            is_timeout = False
            if isinstance(e, requests.exceptions.ReadTimeout):
                is_timeout = True
            elif "ReadTimeout" in str(type(e)) or "timeout" in str(e).lower() or "read timed out" in str(e).lower():
                is_timeout = True
                
            if is_timeout:
                if container:
                    try:
                        container.kill()
                    except:
                        pass
                return {
                    "exit_code": -1,
                    "output": f"Execution timed out after {self.max_execution_time} seconds.",
                    "execution_time_seconds": self.max_execution_time,
                    "status": "timeout"
                }
            
            return {
                "exit_code": -1,
                "output": str(e),
                "execution_time_seconds": round(time.time() - start_time, 2),
                "status": "error"
            }
        finally:
            if container:
                try:
                    container.remove(force=True)
                except:
                    pass
            # Cleanup the script
            if os.path.exists(script_path):
                os.remove(script_path)
