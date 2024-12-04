# s1.py
import subprocess
import numpy as np

from scipy.fftpack import dct, idct  # Import DCT and IDCT from scipy.fftpack

class Converter:
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
        """Resize an image to the specified width and height."""
        command = [
            "ffmpeg", "-i", input_image_path,
            "-vf", f"scale={width}:{height}",
            output_image_path,
            "-y"
        ]
        subprocess.run(command, check=True)
        print(f"Resized image saved as {output_image_path}")

    
    @staticmethod
    def serpentine(matrix):
        """Performs serpentine traversal on a 2D matrix."""
        rows, cols = matrix.shape
        result = []

        i, j = 0, 0
        direction = 1  # 1 for right-down, -1 for left-up

        while len(result) < rows * cols:
            result.append(int(matrix[i, j]))

            if direction == 1:  # Moving right-down
                if j + 1 < cols and i - 1 >= 0:  # Move diagonally down-left
                    j += 1
                    i -= 1
                elif j + 1 < cols:  # Move right
                    j += 1
                    direction = -1
                else:  # Move down
                    i += 1
                    direction = -1
            else:  # Moving left-up
                if i + 1 < rows and j - 1 >= 0:  # Move diagonally up-right
                    i += 1
                    j -= 1
                elif i + 1 < rows:  # Move down
                    i += 1
                    direction = 1
                else:  # Move right
                    j += 1
                    direction = 1

        return result
    
    @staticmethod
    def compress_to_bw(input_image_path, output_image_path):
        """Compress an image to black-and-white (grayscale) with high compression."""
        command = [
            "ffmpeg", "-i", input_image_path,  # Open image
            "-vf", "hue=s=0",  # Convert to grayscale (black and white)
            "-q:v", "31",  # Set the highest compression for JPEG (scale 1-31, where 31 is highest compression)
            output_image_path,
            "-y"  # Overwrite output file if it exists
        ]
        subprocess.run(command, check=True)
        print(f"Compressed black-and-white image saved as {output_image_path}")
        
class DCTConverter:
    @staticmethod
    def apply_dct(data):
        data = np.array(data)
        dct_result = dct(data, norm='ortho')
        return dct_result

    @staticmethod
    def apply_idct(dct_data):
        dct_data = np.array(dct_data)
        idct_result = idct(dct_data, norm='ortho')
        return idct_result

class DWTConverter:

    @staticmethod
    def apply_dwt(data, level=1):
        """
        Apply Discrete Wavelet Transform (DWT) to the given data using the Haar wavelet.
        :param data: The input data to be transformed (must be a power of 2 length).
        :param level: The level of decomposition.
        :return: The wavelet coefficients.
        """
        # Make sure the data length is a power of 2
        if len(data) & (len(data) - 1) != 0:
            raise ValueError("Input data length must be a power of 2")

        coeffs = [data]
        for _ in range(level):
            data = DWTConverter._haar_transform(data)
            coeffs.append(data)

        return coeffs

    @staticmethod
    def _haar_transform(data):
        """
        Apply a single level of the Haar wavelet transform to the data.
        :param data: The input data (even length).
        :return: Transformed data with approximation and detail coefficients.
        """
        N = len(data)
        result = np.zeros(N)
        
        # Step 1: Average (approximation coefficients)
        for i in range(0, N, 2):
            result[i // 2] = (data[i] + data[i + 1]) / 2

        # Step 2: Difference (detail coefficients)
        for i in range(0, N, 2):
            result[N // 2 + i // 2] = (data[i] - data[i + 1]) / 2

        return result

    @staticmethod
    def apply_idwt(coeffs):
        """
        Apply Inverse Discrete Wavelet Transform (IDWT) to the DWT-transformed data.
        :param coeffs: The wavelet coefficients obtained from DWT.
        :return: The data reconstructed from the DWT domain.
        """
        data = coeffs[0]
        for c in reversed(coeffs[1:]):
            data = DWTConverter._haar_inverse_transform(data, c)
        return data

    @staticmethod
    def _haar_inverse_transform(approx, detail):
        """
        Perform the inverse Haar transform by combining approximation and detail coefficients.
        :param approx: The approximation coefficients.
        :param detail: The detail coefficients.
        :return: The reconstructed data.
        """
        N = len(approx) * 2
        result = np.zeros(N)
        
        # Step 1: Combine approximation and detail to reconstruct data
        for i in range(len(approx)):
            result[2 * i] = approx[i] + detail[i]  # Sum of approximation and detail
            result[2 * i + 1] = approx[i] - detail[i]  # Difference of approximation and detail

        return result



