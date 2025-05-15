import os
from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import JSONResponse
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
    data_root = "./checkpoints/ditto_trt_Ampere_Plus"
    cfg_pkl = "./checkpoints/ditto_cfg/v0.4_hubert_cfg_trt.pkl"
    sdk = StreamSDK(cfg_pkl, data_root)

@app.post("/generate")
async def generate_video(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    source_file: UploadFile = File(...),
    more_kwargs: Optional[str] = Form(None),
    output_filename: str = Form("output.mp4")
):
    """
    Generate a talking head video from audio and source image/video
    
    - **audio_file**: Audio file (.wav)
    - **source_file**: Source image or video file
    - **more_kwargs**: JSON string or path to pickle file with additional parameters
    - **output_filename**: Name of the output file (default: output.mp4)
    """
    # Create temporary directory for processing
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Save uploaded files to temporary directory
        audio_path = os.path.join(temp_dir, audio_file.filename)
        with open(audio_path, "wb") as f:
            shutil.copyfileobj(audio_file.file, f)
        
        source_path = os.path.join(temp_dir, source_file.filename)
        with open(source_path, "wb") as f:
            shutil.copyfileobj(source_file.file, f)
        
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
        
        # Run the processing in the background
        background_tasks.add_task(
            process_video,
            sdk=sdk,
            audio_path=audio_path,
            source_path=source_path,
            output_path=output_path,
            more_kwargs=kwargs_dict,
            temp_dir=temp_dir
        )
        
        return JSONResponse(
            content={
                "message": "Processing started",
                "status": "success",
                "output_filename": output_filename
            }
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

async def process_video(
    sdk: StreamSDK,
    audio_path: str,
    source_path: str,
    output_path: str,
    more_kwargs: Union[str, Dict[str, Any]],
    temp_dir: str
):
    """Process the video in the background and clean up temporary files"""
    try:
        # Run the main processing function
        run(sdk, audio_path, source_path, output_path, more_kwargs)
        
        # Here you would typically move the output file to a permanent location
        # or implement a way for the user to download it
        
    finally:
        # Clean up temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
