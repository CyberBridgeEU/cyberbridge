from fastapi import HTTPException, UploadFile
from io import BytesIO
import json
import subprocess
import zipfile


class Utilities:
    # Function to run Semgrep scan and return JSON output
    @staticmethod
    def run_semgrep_scan(path: str, config: str) -> dict:
        try:
            # Run semgrep using subprocess and capture the output
            # Note: check=False because semgrep returns exit code 1 when findings exist,
            # which is expected behavior, not an error. Only exit codes > 1 are real errors.
            result = subprocess.run(
                ["semgrep", "scan", "--config", config, path, "--json"],
                capture_output=True,
                text=True,
                check=False
            )
            # Exit code 0 = no findings, 1 = findings exist (both are valid results)
            # Exit codes > 1 indicate actual errors
            if result.returncode > 1:
                raise HTTPException(status_code=500, detail=f"Semgrep scan failed: {result.stderr}")
            # Parse the output (Semgrep returns JSON formatted data)
            return json.loads(result.stdout)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # Function to unzip the uploaded ZIP file to a temporary directory
    @staticmethod
    def unzip_file(zip_file: UploadFile, temp_dir: str):
        with zipfile.ZipFile(BytesIO(zip_file.file.read()), 'r') as zip_ref:
            zip_ref.extractall(temp_dir)