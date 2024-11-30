from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import FileResponse, JSONResponse
import subprocess
import os

import ffmpeg
from uuid import uuid4

app = FastAPI()

# Directory to save uploaded and processed files
UPLOAD_DIR = "uploads"
PROCESSED_DIR = "processed"

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(PROCESSED_DIR, exist_ok=True)

@app.post("/Modify Resolution")
async def convert_resolution(file: UploadFile, width: int = Form(...), height: int = Form(...)):
    """
    Convert the video resolution using FFmpeg.
    :param file: Uploaded video file.
    :param width: Desired width of the output video.
    :param height: Desired height of the output video.
    :return: Path to the processed file.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"
        output_path = f"processed/{file_id}_converted_{width}x{height}.mp4"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        ffmpeg.input(input_path).output(output_path, vf=f"scale={width}:{height}").run()

        return JSONResponse(content={"output_path": output_path}, status_code=200)
    
    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/Modify the Chroma Subsampling")
async def convert_chroma(file: UploadFile, chroma_format: str = Form(...)):
    """
    Endpoint to modify the chroma subsampling of a video.
    :param file: Uploaded video file.
    :param chroma_format: Desired chroma subsampling format (e.g., 'yuv420p', 'yuv422p', 'yuv444p').
    :return: Path to the processed file.
    """
    try:
        # Save the uploaded file
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"
        output_path = f"processed/{file_id}_chroma_{chroma_format}.mp4"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Use FFmpeg to modify chroma subsampling
        ffmpeg.input(input_path).output(output_path, pix_fmt=chroma_format).run()

        # Return the output path
        return JSONResponse(content={"output_path": output_path}, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/Read video info/")
async def read_video_info(file: UploadFile):
    """
    Extract and return video information using FFmpeg.
    :param file: Uploaded video file.
    :return: JSON response with video metadata.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        probe = ffmpeg.probe(input_path)

        format_info = probe.get("format", {})
        streams = probe.get("streams", [])
        video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})

        # Convert duration to minutes:seconds format
        duration_seconds = float(format_info.get("duration", 0))
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        formatted_duration = f"{minutes}:{seconds:02}"

        video_info = {
            "Duration (s)": formatted_duration,    # Duration in seconds
            "Bitrate (bps)": int(format_info.get("bit_rate", 0)),       # Bitrate in bits per second
            "Width": video_stream.get("width", "Unknown"),        # VIdeo width 
            "Height": video_stream.get("height", "Unknown"),      # Video height
            "Codec": video_stream.get("codec_name", "Unknown"),   # Codec used
            "Format": format_info.get("format_name", "Unknown"),  # File format
        }

        return JSONResponse(content={"message": "Video info extracted", "video_info": video_info}, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg failed to extract video info", "details": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500)


@app.post("/create_bbb_container/")
async def create_bbb_container(file: UploadFile):
    """
    Create a new Big Buck Bunny (BBB) container fulfilling specific requirements:
    - Cut BBB into a 20-second video.
    - Export BBB audio tracks in AAC (mono), MP3 (stereo, lower bitrate), and AC3 codecs.
    - Package everything into a single .mp4 file.

    :param file: Uploaded video file.
    :return: JSON response with output path.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Define paths for outputs
        temp_video = "/tmp/bbb_20s.mp4"
        aac_audio = "/tmp/audio.aac"
        mp3_audio = "/tmp/audio.mp3"
        ac3_audio = "/tmp/audio.ac3"
        final_output = "/tmp/bbb_container.mp4"

        # Cut video to 20 seconds
        subprocess.run(f"ffmpeg -i {input_path} -t 20 {temp_video}", shell=True)

        # Export audio in various formats
        subprocess.run(f"ffmpeg -i {temp_video} -vn -ac 1 {aac_audio}", shell=True)
        subprocess.run(f"ffmpeg -i {temp_video} -vn -b:a 128k {mp3_audio}", shell=True)
        subprocess.run(f"ffmpeg -i {temp_video} -vn -c:a ac3 {ac3_audio}", shell=True)

        # Package everything into a single MP4
        subprocess.run(
            f"ffmpeg -i {temp_video} -i {aac_audio} -i {mp3_audio} -i {ac3_audio} -map 0:v -map 1:a -map 2:a -map 3:a {final_output}",
            shell=True,
        )

        return FileResponse(final_output, media_type="video/mp4")

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg processing failed", "details": error_message}, status_code=400,)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500,)



@app.get("/Download")
async def download_file(file_path: str):
    """
    Download a processed video.
    """
    if not os.path.exists(file_path):
        return {"error": "File does not exist"}
    return FileResponse(file_path, media_type="video/mp4", filename=os.path.basename(file_path))
