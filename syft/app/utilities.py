import os
import subprocess
import json
import zipfile
from io import BytesIO

from fastapi import HTTPException, UploadFile


class Utilities:

    @staticmethod
    def run_syft_scan(command: list) -> dict:
        """Run the Syft CLI command and return the CycloneDX JSON results as a dictionary."""
        try:
            print(f"Executing command: {' '.join(command)}")
            result = subprocess.run(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=os.environ.copy()
            )

            print(f"Return code: {result.returncode}")
            print(f"stderr: {result.stderr}")

            # Even if return code is non-zero, try to parse output if present
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    pass

            # If we couldn't parse JSON output, check for error conditions
            if result.returncode != 0:
                error_msg = f"Command failed with return code {result.returncode}\n"
                error_msg += f"stdout: {result.stdout}\n"
                error_msg += f"stderr: {result.stderr}"
                raise Exception(error_msg)

            # If no output but successful return code, return empty SBOM
            return {"components": [], "message": "No components found"}

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error running Syft: {str(e)}")

    # Function to unzip the uploaded ZIP file to a temporary directory
    @staticmethod
    def unzip_file(zip_file: UploadFile, temp_dir: str):
        with zipfile.ZipFile(BytesIO(zip_file.file.read()), 'r') as zip_ref:
            zip_ref.extractall(temp_dir)
