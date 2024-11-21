from fastapi import FastAPI, File, UploadFile, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
import numpy as np
import shutil
import os
from S1 import Converter, DCTConverter, DWTConverter  # Import the Converter class

app = FastAPI()

# Create a static folder to store processed files
static_dir = "static"
os.makedirs(static_dir, exist_ok=True)

# Mount the static directory to serve images directly from it
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def root():
    return """
    <html>
        <head><title>Image Processor</title></head>
        <body>
            <h1>Welcome to the Image Processor API</h1>
            <p>Use the available endpoints to resize or convert images.</p>
            <ul>
                <li><strong>/resize_image</strong>: Resize an image</li>
                <li><strong>/compress_to_bw</strong>: Convert an image to black-and-white</li>
            </ul>
        </body>
    </html>
    """

@app.get("/convert_rgb_to_yuv")
async def convert_rgb_to_yuv(r: int, g: int, b: int):
    y, u, v = Converter.rgb_to_yuv(r, g, b)
    return {"y": y, "u": u, "v": v}

@app.get("/convert_yuv_to_rgb")
async def convert_yuv_to_rgb(y: float, u: float, v: float):
    r, g, b = Converter.yuv_to_rgb(y, u, v)
    return {"r": r, "g": g, "b": b}

@app.post("/resize_image")
async def resize_image(
    request: Request,  # Move this up as it is a non-default argument
    file: UploadFile = File(...),
    width: int = 800,
    height: int = 600
):
    # Save the uploaded file temporarily
    input_image_path = f"temp_{file.filename}"
    with open(input_image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Define output image path in static directory
    output_image_path = f"{static_dir}/resized_{file.filename}"
    
    # Call the resize method from the Converter class
    Converter.resize_image(input_image_path, output_image_path, width, height)
    
    # Generate the full URL of the processed image (http://localhost:8000/static/... or https://...)
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    image_url = f"{base_url}/static/{os.path.basename(output_image_path)}"
    
    # Return the full URL to the resized image
    return {"message": "Resized image processed", "image_url": image_url}

@app.get("/serpentine")
def serpentine_traversal():
    try:
        # Example 2D matrix
        matrix = np.array([
            [1, 2, 3, 4],
            [5, 6, 7, 8],
            [9, 10, 11, 12],
            [13, 14, 15, 16]
        ])
        
        # Apply serpentine traversal
        result = Converter.serpentine(matrix)
        
        return {
            "original_matrix": matrix.tolist(),
            "serpentine_result": result
        }
    except Exception as e:
        return {"error": str(e)}  # Return the error as a response


@app.post("/compress_to_bw")
async def compress_to_bw(
    request: Request,  # Inject Request to get the full URL
    file: UploadFile = File(...)
):
    # Save the uploaded file temporarily
    input_image_path = f"temp_{file.filename}"
    with open(input_image_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Define output image path in the static directory
    output_image_path = f"{static_dir}/bw_{file.filename}"
    
    # Call the compress-to-bw method from the Converter class
    Converter.compress_to_bw(input_image_path, output_image_path)
    
    # Generate the full URL of the processed image
    base_url = f"{request.url.scheme}://{request.url.netloc}"
    image_url = f"{base_url}/static/{os.path.basename(output_image_path)}"
    
    # Return the full URL to the compressed black-and-white image
    return {"message": "Black-and-white image processed", "image_url": image_url}

@app.get("/dct")
def apply_dct_and_idct():
    data_1d = [255, 128, 64, 32, 16, 8, 4, 2]
    dct_1d = DCTConverter.apply_dct(data_1d)
    idct_1d = DCTConverter.apply_idct(dct_1d)

    data_2d = np.array([
        [255, 128, 64, 32],
        [16, 8, 4, 2],
        [255, 128, 64, 32],
        [16, 8, 4, 2]
    ])
    dct_2d = DCTConverter.apply_dct(data_2d)
    idct_2d = DCTConverter.apply_idct(dct_2d)

    return {
        "original_1d": data_1d,
        "dct_1d": dct_1d.tolist(),
        "reconstructed_1d": idct_1d.tolist(),
        "original_2d": data_2d.tolist(),
        "dct_2d": dct_2d.tolist(),
        "reconstructed_2d": np.round(idct_2d).tolist()
    }
    
@app.get("/dwt")
def apply_dwt_and_idwt():
    # Sample 1D data for DWT and IDWT
    data_1d = [255, 128, 64, 32, 16, 8, 4, 2]
    
    # Apply DWT and IDWT on 1D data
    dwt_1d = DWTConverter.apply_dwt(data_1d)
    idwt_1d = DWTConverter.apply_idwt(dwt_1d)

    # Sample 2D data for DWT and IDWT
    data_2d = np.array([
        [255, 128, 64, 32],
        [16, 8, 4, 2],
        [255, 128, 64, 32],
        [16, 8, 4, 2]
    ])
    
    # Apply DWT and IDWT on 2D data (decompose and reconstruct)
    dwt_2d = DWTConverter.apply_dwt(data_2d.tolist())  # Convert to list for the function
    idwt_2d = DWTConverter.apply_idwt(dwt_2d)

    return {
        "original_1d": data_1d,
        "dwt_1d": [coeff.tolist() for coeff in dwt_1d],  # Convert to list for response
        "reconstructed_1d": idwt_1d.tolist(),
        "original_2d": data_2d.tolist(),
        "dwt_2d": [coeff.tolist() for coeff in dwt_2d],  # Convert to list for response
        "reconstructed_2d": np.round(idwt_2d).tolist()
    }