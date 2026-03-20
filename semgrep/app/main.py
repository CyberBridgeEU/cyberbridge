import os, shutil, uuid
from fastapi import FastAPI, HTTPException, UploadFile, File
from app.utilities import Utilities
from fastapi.middleware.cors import CORSMiddleware


# FastAPI instance
app = FastAPI()

# Add CORS middleware with explicit configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Temporary: allow all origins for testing
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.get("/", response_model=dict)
async def check_health():
    """
    Endpoint to check the service's health status.
    Returns a JSON response confirming the API is running.
    """
    return {"message": "semgrep rest api is up and running!"}

@app.post("/scan-zip", response_model=dict)
async def scan_zip(file: UploadFile = File(...), config: str = "auto"):
    """
    Endpoint to upload a ZIP file containing source code, unzip it,
    and run Semgrep scan on the extracted files.
    - `file`: The ZIP file containing source code files.
    - `config`: The rules or configuration to use for scanning (default: "auto").
    Returns the Semgrep results in JSON format.
    """
    # Create a unique temporary directory for this request
    unique_id = str(uuid.uuid4())
    temp_dir = os.path.join("/tmp/semgrep_files", unique_id)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Unzip the uploaded file into the temporary directory
        Utilities.unzip_file(file, temp_dir)

        # Run Semgrep scan on the extracted files
        results = Utilities.run_semgrep_scan(temp_dir, config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process ZIP file: {str(e)}")
    finally:
        # Clean up the temporary directory and all its contents
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

    return results
