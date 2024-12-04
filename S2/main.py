from fastapi import FastAPI, File, UploadFile, Request, Form
from fastapi.responses import FileResponse, JSONResponse
from uuid import uuid4
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
async def create_bbb_container(uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    - Cuts the input video to 20 seconds.
    - Extract audio tracks in AAC, MP3, and AC3 formats.
    - Combine all into a single MP4 file.
    
    :param uploaded_file: The uploaded video file to process.
    :param container_name: Name for the final video (optional).
    :return: The final processed MP4 file.
    """
    try:
        # Generate a unique identifier to avoid overwriting files
        unique_id = str(uuid4())

        # Save the uploaded file locally in the 'processed' folder
        saved_path = f"processed/{unique_id}_{uploaded_file.filename}"
        with open(saved_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Use a default name if no custom name is provided
        if not container_name:
            container_name = f"container_{unique_id}"

        # Paths for intermediate and final outputs
        trimmed_video = f"processed/{container_name}_20s.mp4"
        audio_aac = f"processed/{container_name}_audio.aac"
        audio_mp3 = f"processed/{container_name}_audio.mp3"
        audio_ac3 = f"processed/{container_name}_audio.ac3"
        final_video = f"processed/{container_name}_final.mp4"

        # Trim the video to 20 seconds
        subprocess.run(f"ffmpeg -i {saved_path} -t 20 {trimmed_video}", shell=True)

        # Extract audio in different formats
        subprocess.run(f"ffmpeg -i {trimmed_video} -vn -ac 1 {audio_aac}", shell=True)  # AAC (mono)
        subprocess.run(f"ffmpeg -i {trimmed_video} -vn -b:a 128k {audio_mp3}", shell=True)  # MP3 (stereo, 128k bitrate)
        subprocess.run(f"ffmpeg -i {trimmed_video} -vn -c:a ac3 {audio_ac3}", shell=True)  # AC3 format

        # Combine everything into a single MP4 container
        subprocess.run(
            f"ffmpeg -i {trimmed_video} -i {audio_aac} -i {audio_mp3} -i {audio_ac3} -map 0:v -map 1:a -map 2:a -map 3:a {final_video}",
            shell=True,
        )

        # Return the final processed video file
        return FileResponse(final_video, media_type="video/mp4")

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg processing failed", "details": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500)


@app.post("/read_mp4_tracks/")
async def read_mp4_tracks(uploaded_file: UploadFile):
    """
    Reads the number of tracks (audio and video) in an MP4 container.
    
    :param uploaded_file: The uploaded MP4 file to analyze.
    :return: returns the number of tracks (audio/video).
    """
    try:
        # Save the uploaded file locally
        unique_id = str(uuid4())
        file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        with open(file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Probe the file to get metadata
        probe = ffmpeg.probe(file_path)

        # Get the streams (audio, video, etc.)
        streams = probe.get("streams", [])
        
        # Count the video and audio tracks
        num_video_tracks = len([stream for stream in streams if stream.get("codec_type") == "video"])
        num_audio_tracks = len([stream for stream in streams if stream.get("codec_type") == "audio"])

        total_tracks = num_video_tracks + num_audio_tracks

        return JSONResponse(content={
            "message": "Track info extracted",
            "video_tracks": num_video_tracks,
            "audio_tracks": num_audio_tracks,
            "total_tracks": total_tracks
        }, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg failed to extract track info", "details": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500)

@app.post("/show_macroblocks_motion_vectors/")
async def show_macroblocks_motion_vectors(uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    Generates a video showing the macroblocks and motion vectors.
    
    :param uploaded_file: The uploaded video file to process.
    :param container_name: Desired name for the processed video (optional).
    :return: Processed video showing motion vectors and macroblocks.
    """
    try:
        # Generate a unique file path for saving the uploaded video
        unique_id = str(uuid4())
        input_file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        # Save the uploaded file locally
        with open(input_file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Use a default name if no custom name is provided
        if not container_name:
            container_name = f"macroblocks_motion_{unique_id}"

        # Path to save the processed video showing motion vectors
        output_file_path = f"processed/{container_name}_motion_vectors.mp4"

        # FFmpeg command to generate motion vectors and macroblocks in the video
        ffmpeg_cmd = f"ffmpeg -flags2 +export_mvs -i {input_file_path} -vf codecview=mv=pf+bf+bb {output_file_path}"
        
        # Run the FFmpeg command
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        return {"message": "Video processed successfully!", "output_file": output_file_path}

    except subprocess.CalledProcessError as e:
        return {"error": f"FFmpeg command failed with error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/show_yuv_histogram/")
async def show_yuv_histogram(uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    Generate a video showing the YUV histograms of the input video.
    
    :param uploaded_file: The uploaded video file to process.
    :param container_name: Desired name for the processed video (optional).
    :return: Processed video showing the YUV histograms.
    """
    try:
        # Generate a unique file path for saving the uploaded video
        unique_id = str(uuid4())
        input_file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        # Save the uploaded file locally
        with open(input_file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Use a default name if no custom name is provided
        if not container_name:
            container_name = f"yuv_histogram_{unique_id}"

        # Path to save the processed video showing YUV histograms
        output_file_path = f"processed/{container_name}_histograms.mp4"

        # FFmpeg command to generate YUV histograms
        ffmpeg.input(input_file_path).output(
            output_file_path,
            vf="histogram=display_mode=stack",
            vcodec="libx264",  # Explicit codec to ensure compatibility
            pix_fmt="yuv420p",  # Set pixel format for MP4 compatibility
            preset="fast"  # Speed/quality tradeoff setting
        ).overwrite_output().run()

        return {"message": "Video processed successfully!", "output_file": output_file_path}

    except ffmpeg.Error as e:
        return {"error": e.stderr.decode()}
    except Exception as e:
        return {"error": str(e)}


@app.get("/Download")
async def download_file(file_path: str):
    """
    Download a processed video.
    """
    if not os.path.exists(file_path):
        return {"error": "File does not exist"}
    return FileResponse(file_path, media_type="video/mp4", filename=os.path.basename(file_path))
