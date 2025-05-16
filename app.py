import os
import uuid
from fastapi import FastAPI, UploadFile, File, Form, Depends
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import shutil
import uvicorn
from typing import Optional, Dict, Any, Union
import json

from inference import StreamSDK, run, load_pkl

app = FastAPI(title="Ditto TalkingHead API", description="API for generating talking head videos")

# Global SDK instance
sdk = None

@app.on_event("startup")
async def startup_event():
    global sdk
    # Default paths from the original script
    data_root = "/root/autodl-fs/ditto-checkpoints/ditto_trt_Ampere_Plus"
    cfg_pkl = "/root/autodl-fs/ditto-checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl"
    sdk = StreamSDK(cfg_pkl, data_root)

# Custom dependency for optional file upload that handles empty strings
async def optional_audio_file(audio_file: Optional[UploadFile] = File(default=None)):
    if audio_file is None or audio_file.filename == "":
        return None
    return audio_file

async def optional_source_file(source_file: Optional[UploadFile] = File(default=None)):
    if source_file is None or source_file.filename == "":
        return None
    return source_file

@app.post("/generate")
async def generate_video(
    audio_file: Optional[UploadFile] = Depends(optional_audio_file),
    source_file: Optional[UploadFile] = Depends(optional_source_file),
    more_kwargs: Optional[str] = Form(None)
):
    """
    Generate a talking head video from audio and source image/video and return it for download
    
    - **audio_file**: Audio file (.wav), defaults to ./example/audio.wav if not provided
    - **source_file**: Source image or video file, defaults to ./example/image.png if not provided
    - **more_kwargs**: JSON string or path to pickle file with additional parameters
    """
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Handle audio file - use default if not provided
        if audio_file is None:
            audio_path = "./example/audio.wav"
        else:
            audio_path = os.path.join(temp_dir, audio_file.filename)
            with open(audio_path, "wb") as f:
                shutil.copyfileobj(audio_file.file, f)
        
        # Handle source file - use default if not provided
        if source_file is None:
            source_path = "./example/image.png"
        else:
            source_path = os.path.join(temp_dir, source_file.filename)
            with open(source_path, "wb") as f:
                shutil.copyfileobj(source_file.file, f)
        
        # Generate a random filename for the output
        output_filename = f"output_{uuid.uuid4().hex}.mp4"
        
        # Set output path
        output_path = os.path.join(temp_dir, output_filename)
        
        # Parse more_kwargs
        kwargs_dict = {}
        if more_kwargs:
            try:
                # Try to parse as JSON
                kwargs_dict = json.loads(more_kwargs)
            except json.JSONDecodeError:
                # If not JSON, treat as path to pickle file
                kwargs_dict = more_kwargs
        
        # Run the processing directly
        run(sdk, audio_path, source_path, output_path, kwargs_dict)
        
        # Check if the output file exists
        if not os.path.exists(output_path):
            raise FileNotFoundError(f"Output file was not generated at {output_path}")
        
        # Create a copy of the file in a more permanent location
        # This ensures the file exists when it's being sent to the client
        permanent_dir = os.path.join(os.getcwd(), "outputs")
        os.makedirs(permanent_dir, exist_ok=True)
        permanent_path = os.path.join(permanent_dir, output_filename)
        shutil.copy2(output_path, permanent_path)
        
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        
        # Return the file as a response from the permanent location
        return FileResponse(
            path=permanent_path,
            filename=output_filename,
            media_type="video/mp4"
        )
    
    except Exception as e:
        # Clean up in case of error
        shutil.rmtree(temp_dir, ignore_errors=True)
        return JSONResponse(
            status_code=500,
            content={
                "message": f"Error processing request: {str(e)}",
                "status": "error"
            }
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=6006, reload=True)
