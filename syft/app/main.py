import os
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil
import uuid
from app.utilities import Utilities

# Initialize FastAPI app
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


@app.get("/")
async def root():
    return {"message": "syft sbom rest api is up and running!"}

@app.post("/scan/zip")
async def scan_zip(file: UploadFile = File(...)):
    """
    Upload a ZIP file, extract it to a temporary directory, generate SBOM with Syft, and return the results.
    The temporary folder is deleted after scanning to prevent storage issues.
    """
    if not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed.")

    # Create a unique temp directory to avoid race conditions
    unique_id = str(uuid.uuid4())
    temp_dir = os.path.join("/tmp/syft_scan_files", unique_id)
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Unzip the uploaded file into the temporary directory
        Utilities.unzip_file(file, temp_dir)

        # Run Syft on the extracted folder to generate CycloneDX JSON SBOM
        command = ["syft", f"dir:{temp_dir}", "-o", "cyclonedx-json"]
        scan_results = Utilities.run_syft_scan(command)

        return scan_results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing ZIP file: {str(e)}")
    finally:
        # Cleanup: Remove the temporary folder
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)
