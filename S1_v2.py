import subprocess
import numpy as np

from scipy.fftpack import dct, idct
from PIL import Image


class Converter: #EX 1-5
    @staticmethod
    def rgb_to_yuv(r, g, b):
        y = 0.257 * r + 0.504 * g + 0.098 * b + 16
        u = -0.148 * r - 0.291 * g + 0.439 * b + 128
        v = 0.439 * r - 0.368 * g - 0.071 * b + 128
        return y, u, v

    @staticmethod
    def yuv_to_rgb(y, u, v):
        r = 1.164 * (y - 16) + 2.018 * (u - 128)
        g = 1.164 * (y - 16) - 0.813 * (v - 128) - 0.391 * (u - 128)
        b = 1.164 * (y - 16) + 1.596 * (v - 128)
        return r, g, b
    
    @staticmethod
    def resize_image(input_image_path, output_image_path, width, height):
        image = Image.open(input_image_path)
        new_image = image.resize((width, height))
        new_image.save(output_image_path)
        print(f"Resized image saved as {output_image_path}")
        
    @staticmethod
    def serpentine(file_path, width):
        with open(file_path, "rb") as f:
            image = f.read()
            path = []
        row, col = 0, 0
        direction = 'right'  # start by moving to the right

        for _ in range(n * n):
            path.append((row, col))

            if direction == 'right':
                if col + 1 < n and (row, col + 1) not in path:
                    col += 1
                else:
                    row += 1
                    direction = 'down'
            elif direction == 'down':
                if row + 1 < n and (row + 1, col) not in path:
                    row += 1
                else:
                    col -= 1
                    direction = 'left'
            elif direction == 'left':
                if col - 1 >= 0 and (row, col - 1) not in path:
                    col -= 1
                else:
                    row -= 1
                    direction = 'up'
            elif direction == 'up':
                if row - 1 >= 0 and (row - 1, col) not in path:
                    row -= 1
                else:
                    col += 1
                    direction = 'right'
    
        # Read bytes in the serpentine order
        serpentine_bytes = [pixels[row, col] for row, col in path]

        return serpentine_bytes
    
    @staticmethod
    def compress_to_bw(input_image_path, output_image_path):
        command = [
            "ffmpeg", "-i", input_image_path, #open image
            "-vf", "hue=s=0",  # Convert to grayscale (black and white)
            "-q:v", "31",  # Set the highest compression for JPEG (scale 1-31, where 31 is highest compression)
            output_image_path,
            "-y"  # Overwrite 
        ]
        # Run the FFmpeg command
        subprocess.run(command, check=True)
        print(f"Compressed black-and-white image saved as {output_image_path}")
        
    @staticmethod
    def run_length_encode(byte_series):
        if not byte_series:
            return []

        encoded_series = []
        count = 1

        # Traverse through byte series to apply RLE
        for i in range(1, len(byte_series)):
            if byte_series[i] == byte_series[i - 1]:
                count += 1
            else:
                encoded_series.append((byte_series[i - 1], count))
                count = 1

        # Append the last byte and its count
        encoded_series.append((byte_series[-1], count))

        return encoded_series
    
############################################################
    
class DCTConverter: #EX 6

    @staticmethod
    def apply_dct(data):
        """
        Apply Discrete Cosine Transform (DCT) to the given data.
        :param data: The input data to be transformed.
        :return: The DCT-transformed data.
        """
        # Convert data to a numpy array for DCT processing
        data = np.array(data)
        
        # Perform DCT (Discrete Cosine Transform)
        dct_result = dct(data, norm='ortho')
        return dct_result

    @staticmethod
    def apply_idct(dct_data):
        """
        Apply Inverse Discrete Cosine Transform (IDCT) to the DCT-transformed data.
        :param dct_data: The data in the DCT domain.
        :return: The data reconstructed from the DCT domain.
        """
        # Convert DCT data to a numpy array
        dct_data = np.array(dct_data)
        
        # Perform IDCT (Inverse Discrete Cosine Transform)
        idct_result = idct(dct_data, norm='ortho')
        return idct_result
    
############################################################


#EX 1       
y, u, v = Converter.rgb_to_yuv(255, 0, 0)  
print(f"RGB (255,0,0) to YUV: ({y}, {u}, {v})")

r, g, b = Converter.yuv_to_rgb(y, u, v)  
print(f"YUV ({y}, {u}, {v}) back to RGB: ({r}, {g}, {b})")
#########################################

#EX 2
Converter.resize_image("input.jpg", "output.jpg", 640, 480)  
#########################################

#EX 3
serpentine_data = Converter.serpentine("input.jpg", width=16)
print(serpentine_data)  # This will print out the bytes in serpentine order
#########################################

#EX 4
Converter.compress_to_bw("input.jpg", "output_bw.jpg")
#########################################

#EX 5
bytes_series = [255, 255, 255, 0, 0, 1, 1, 1, 1, 255]
encoded_series = Converter.run_length_encode(bytes_series)
print("Encoded series:", encoded_series)
#########################################

#EX 6
data_1d = np.array([255, 128, 64, 32, 16, 8, 4, 2])
dct_1d = DCTConverter.apply_dct(data_1d)
idct_1d = DCTConverter.apply_idct(dct_1d)
print("Original 1D data:", data_1d)
print("DCT of 1D data:", dct_1d)
print("Reconstructed 1D data:", idct_1d)

# 2D example (e.g., an image block)
data_2d = np.array([
    [255, 128, 64, 32],
    [16, 8, 4, 2],
    [255, 128, 64, 32],
    [16, 8, 4, 2]
])
dct_2d = DCTConverter.apply_dct(data_2d)
idct_2d = DCTConverter.apply_idct(dct_2d)
print("\nOriginal 2D data:\n", data_2d)
print("\nDCT of 2D data:\n", dct_2d)
print("\nReconstructed 2D data:\n", np.round(idct_2d))
#########################################´

#EX 7 



#########################################