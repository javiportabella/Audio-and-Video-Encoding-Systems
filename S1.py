import subprocess
import numpy as np
import pywt

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
    def serpentine(matrix):
        n = matrix.shape[0]  
        result = [None] * (n * n)  
        
        a = 0  
        i = 0 
        j = 0 
        result[a] = matrix[i, j]  # First value
        
        while a < n * n - 1:  
            #step 1: (one to the right)
            if j == n - 1:  
                i += 1
            else:
                j += 1

            a += 1
            if a < n * n:
                result[a] = matrix[i, j]
            
            #step 2: (Diagonal down to the left until reaching j = 0)
            while i + 1 < n and j - 1 >= 0 and a < n * n - 1:
                i += 1
                j -= 1
                a += 1
                result[a] = matrix[i, j]
            
            #step 3: (one down)
            if i == n - 1:  
                j += 1
            else:
                i += 1

            a += 1
            if a < n * n:
                result[a] = matrix[i, j]
            
            #step 4: (Diagonal up to the right until reaching i = 0)
            while j + 1 < n and i - 1 >= 0 and a < n * n - 1:
                i -= 1
                j += 1
                a += 1
                result[a] = matrix[i, j]
        
        return result
    
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

class DWTConverter:  # EX 7

    @staticmethod
    def apply_dwt(data, wavelet='haar', level=1):
        """
        Apply Discrete Wavelet Transform (DWT) to the given data.
        :param data: The input data to be transformed.
        :param wavelet: Type of wavelet to be used for the DWT (default is 'haar').
        :param level: Level of decomposition (default is 1).
        :return: The DWT-transformed data.
        """
        # Convert data to a numpy array for DWT processing
        data = np.array(data)
        
        # Perform DWT (Discrete Wavelet Transform)
        coeffs = pywt.wavedec(data, wavelet=wavelet, level=level)
        return coeffs

    @staticmethod
    def apply_idwt(coeffs, wavelet='haar'):
        """
        Apply Inverse Discrete Wavelet Transform (IDWT) to the DWT-transformed data.
        :param coeffs: The wavelet coefficients obtained from DWT.
        :param wavelet: Type of wavelet used for the inverse transformation (default is 'haar').
        :return: The data reconstructed from the DWT domain.
        """
        # Perform IDWT (Inverse Discrete Wavelet Transform)
        idwt_result = pywt.waverec(coeffs, wavelet=wavelet)
        return idwt_result

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
matrix = np.array([
    [1,  2,  3,  4],
    [5,  6,  7,  8],
    [9, 10, 11, 12],
    [13, 14, 15, 16]
])

result = Converter.serpentine(matrix)
print("Serpentine traversal of the matrix:", result)
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
data_1d = [255, 128, 64, 32, 16, 8, 4, 2]
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
data_1d = [255, 128, 64, 32, 16, 8, 4, 2]
dct_1d = DWTConverter.apply_dwt(data_1d)
idct_1d = DWTConverter.apply_idwt(dct_1d)
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
dct_2d = DWTConverter.apply_dwt(data_2d)
idct_2d = DWTConverter.apply_idwt(dct_2d)
print("\nOriginal 2D data:\n", data_2d)
print("\nDCT of 2D data:\n", dct_2d)
print("\nReconstructed 2D data:\n", np.round(idct_2d))
#########################################