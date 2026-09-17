import pytest
import os
from backend.sandbox.executor import SandboxExecutor
from backend.tools.builtins import exec_generate_docx, exec_generate_xlsx, exec_generate_pptx

@pytest.fixture
def executor():
    return SandboxExecutor(max_execution_time=10)

def test_sandbox_network_disabled(executor):
    code = """
import urllib.request
try:
    urllib.request.urlopen("http://example.com", timeout=2)
    print("SUCCESS")
except Exception as e:
    print(f"FAILED: {e}")
"""
    result = executor.execute(code)
    assert "FAILED" in result["output"]
    assert "SUCCESS" not in result["output"]

def test_sandbox_timeout(executor):
    code = """
import time
while True:
    time.sleep(1)
"""
    result = executor.execute(code)
    assert result["status"] == "timeout"
    assert result["execution_time_seconds"] >= 4

def test_sandbox_basic_math(executor):
    code = """
print(2 + 2)
"""
    result = executor.execute(code)
    assert result["status"] == "success"
    assert "4" in result["output"]

def test_path_traversal_blocked_artifacts():
    res_docx = exec_generate_docx("test", "../test.docx")
    assert "Path traversal is not allowed" in res_docx
    
    res_xlsx = exec_generate_xlsx("[[1]]", "/etc/passwd.xlsx")
    assert "Path traversal is not allowed" in res_xlsx
    
    res_pptx = exec_generate_pptx('[{"title":"a","content":"b"}]', "../../root.pptx")
    assert "Path traversal is not allowed" in res_pptx
