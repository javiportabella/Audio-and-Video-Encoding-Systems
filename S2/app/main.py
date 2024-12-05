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
async def convert_resolution(request: Request, file: UploadFile, width: int = Form(...), height: int = Form(...)):
    """
    This endpoint modifies the resolution of an uploaded video file by applying the specified width and height, 
    returning the processed video.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"
        output_path = f"processed/{file_id}_converted_{width}x{height}.mp4"

        # Save the uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Run FFmpeg command to modify the resolution
        ffmpeg.input(input_path).output(output_path, vf=f"scale={width}:{height}").run()

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_path}"

        # Return the success message with the download link
        return JSONResponse(content={
            "message": "Video processed successfully!",
            "download_link": download_url
        }, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)


@app.post("/Modify the Chroma Subsampling")
async def convert_chroma(request: Request, file: UploadFile, chroma_format: str = Form(...)):
    """
    This endpoint changes the chroma subsampling format of an uploaded video to the specified format, 
    returning the processed video.
    """
    try:
        file_id = str(uuid4())
        input_path = f"processed/{file_id}_{file.filename}"
        output_path = f"processed/{file_id}_chroma_{chroma_format}.mp4"

        # Save the uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # Run FFmpeg command to change chroma subsampling
        ffmpeg.input(input_path).output(output_path, pix_fmt=chroma_format).run()

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_path}"

        # Return success message with the download link
        return JSONResponse(content={
            "message": "Video processed successfully!",
            "download_link": download_url
        }, status_code=200)

    except ffmpeg.Error as e:
        # Check if stderr is None before trying to decode it
        error_message = e.stderr.decode() if e.stderr else "Unknown FFmpeg error"
        return JSONResponse(content={"error": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)
    
@app.post("/Read video info/")
async def read_video_info(request: Request, file: UploadFile):
    """
    This endpoint extracts and displays metadata from an uploaded video file, 
    including details like duration, bitrate, resolution, codec, and format.
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

        duration_seconds = float(format_info.get("duration", 0))
        minutes = int(duration_seconds // 60)
        seconds = int(duration_seconds % 60)
        formatted_duration = f"{minutes}:{seconds:02}"

        video_info = {
            "Duration (s)": formatted_duration,
            "Bitrate (bps)": int(format_info.get("bit_rate", 0)),
            "Width": video_stream.get("width", "Unknown"),
            "Height": video_stream.get("height", "Unknown"),
            "Codec": video_stream.get("codec_name", "Unknown"),
            "Format": format_info.get("format_name", "Unknown"),
        }

        return JSONResponse(content={"message": "Video info extracted", "video_info": video_info}, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg failed to extract video info", "details": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500)


@app.post("/create_bbb_container/")
async def create_bbb_container(request: Request, uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    This endpoint trims the input video to 20 seconds, extracts audio in multiple formats (AAC, MP3, AC3), 
    and combines them into a single MP4 file. Where you can download each process.
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

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct full download URLs
        cut_video_url = f"{base_url}/Download?file_path={trimmed_video}"
        mp3_audio_url = f"{base_url}/Download?file_path={audio_mp3}"
        aac_audio_url = f"{base_url}/Download?file_path={audio_aac}"
        ac3_audio_url = f"{base_url}/Download?file_path={audio_ac3}"
        final_video_url = f"{base_url}/Download?file_path={final_video}"

        # Return the download links for all the files
        return {
            "message": "Video processed successfully!",
            "download_links": {
                "cut_video": cut_video_url,
                "mp3_audio": mp3_audio_url,
                "aac_audio": aac_audio_url,
                "ac3_audio": ac3_audio_url,
                "final_video": final_video_url,
            }
        }

    except subprocess.CalledProcessError as e:
        return {"error": f"FFmpeg command failed with error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}


@app.post("/read_mp4_tracks/")
async def read_mp4_tracks(request: Request, uploaded_file: UploadFile):
    """
    This endpoint extracts and summarizes track information from an uploaded MP4 file, 
    returning the count of video and audio tracks present.
    """
    try:
        unique_id = str(uuid4())
        file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        with open(file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        probe = ffmpeg.probe(file_path)

        streams = probe.get("streams", [])
        video_tracks = [s for s in streams if s.get("codec_type") == "video"]
        audio_tracks = [s for s in streams if s.get("codec_type") == "audio"]

        track_info = {
            "video_tracks": len(video_tracks),
            "audio_tracks": len(audio_tracks),
        }

        return JSONResponse(content={"message": "Track info extracted", "track_info": track_info}, status_code=200)

    except ffmpeg.Error as e:
        error_message = e.stderr.decode()
        return JSONResponse(content={"error": "FFmpeg failed to extract track info", "details": error_message}, status_code=400)
    except Exception as e:
        return JSONResponse(content={"error": "An unexpected error occurred", "details": str(e)}, status_code=500)


@app.post("/show_macroblocks_motion_vectors/")
async def show_macroblocks_motion_vectors(request: Request, uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    This endpoint processes a video to show the motion vectors of macroblocks.
    It returns a video with motion vectors overlayed, and a download link to access the processed video.
    """
    try:
        unique_id = str(uuid4())
        input_file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        # Save the uploaded file locally
        with open(input_file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Set default name if container_name is not provided
        if not container_name:
            container_name = f"macroblocks_motion_{unique_id}"

        # Define output file path
        output_file_path = f"processed/{container_name}_motion_vectors.mp4"

        # Run FFmpeg command to process motion vectors
        ffmpeg_cmd = f"ffmpeg -flags2 +export_mvs -i {input_file_path} -vf codecview=mv=pf+bf+bb {output_file_path}"
        subprocess.run(ffmpeg_cmd, shell=True, check=True)

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_file_path}"

        # Return success message with the download link
        return {
            "message": "Video processed successfully!",
            "download_link": download_url
        }

    except subprocess.CalledProcessError as e:
        return {"error": f"FFmpeg command failed with error: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}
    
@app.post("/show_yuv_histogram/")
async def show_yuv_histogram(request: Request, uploaded_file: UploadFile, container_name: str = Form(None)):
    """
    This endpoint generates a YUV histogram visualization of a video.
    It returns a video with the YUV histogram and a download link to access the processed video.
    """
    try:
        unique_id = str(uuid4())
        input_file_path = f"processed/{unique_id}_{uploaded_file.filename}"

        # Save the uploaded file locally
        with open(input_file_path, "wb") as temp_file:
            temp_file.write(await uploaded_file.read())

        # Set default name if container_name is not provided
        if not container_name:
            container_name = f"yuv_histogram_{unique_id}"

        # Define output file path
        output_file_path = f"processed/{container_name}_histograms.mp4"

        # Run FFmpeg command to generate YUV histogram
        ffmpeg.input(input_file_path).output(
            output_file_path,
            vf="histogram=display_mode=stack",  # Apply the YUV histogram filter
            vcodec="libx264",  # Use x264 codec for video encoding
            pix_fmt="yuv420p",  # Set pixel format to yuv420p
            preset="fast"  # Use fast encoding preset
        ).overwrite_output().run()

        # Generate the base URL of the server
        base_url = f"{request.url.scheme}://{request.url.netloc}"

        # Construct the full download URL
        download_url = f"{base_url}/Download?file_path={output_file_path}"

        # Return success message with the download link
        return {
            "message": "Video processed successfully!",
            "download_link": download_url
        }

    except ffmpeg.Error as e:
        return {"error": e.stderr.decode()}
    except Exception as e:
        return {"error": str(e)}

@app.get("/Download")
async def download_file(request: Request, file_path: str):
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type='application/octet-stream', filename=os.path.basename(file_path))
    else:
        return JSONResponse(content={"error": "File not found"}, status_code=404)
