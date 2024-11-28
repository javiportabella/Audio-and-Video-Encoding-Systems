# s1.py
import subprocess
import numpy as np

from scipy.fftpack import dct, idct

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
            "ffmpeg", "-i", input_image_path,  # opening the image in the path
            "-vf", "hue=s=0",  # convert to grayscale
            "-q:v", "31",
            output_image_path,
            "-y"  #overwrite output file if it exiists
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
        :param data: The input data to be transformed (1D or 2D, must have even dimensions).
        :param level: The number of decomposition levels.
        :return: List of wavelet coefficients (approximation + detail).
        """
        data = np.array(data)  # Convertir a numpy array para facilidad
        coeffs = []

        for _ in range(level):
            transformed_data = DWTConverter._haar_transform(data)  # Aplicar Haar
            coeffs.append(transformed_data)  # Guardar datos transformados
            if data.ndim == 1:
                #parte de aproximación para el siguiente nivel (primera mitad)
                data = transformed_data[:len(transformed_data) // 2]
            elif data.ndim == 2:
                #parte superior izquierda (aproximación) para el siguiente nivel
                rows, cols = transformed_data.shape
                data = transformed_data[:rows // 2, :cols // 2]

        return coeffs


    @staticmethod
    def _haar_transform(data):
        """
        Apply a single level of the Haar wavelet transform to the data.
        Handles both 1D and 2D cases.
        :param data: The input data (1D or 2D, must have even dimensions).
        :return: Transformed data with approximation and detail coefficients.
        """
        data = np.array(data)

        if data.ndim == 1:
            # Transformación 1D
            N = len(data)
            approx = [(data[i] + data[i + 1]) / 2 for i in range(0, N, 2)]
            detail = [(data[i] - data[i + 1]) / 2 for i in range(0, N, 2)]
            return np.array(approx + detail)

        elif data.ndim == 2:
            # Transformación 2D (filas y luego columnas)
            row_transformed = np.array([DWTConverter._haar_transform(row) for row in data])  # Filas
            col_transformed = np.array([DWTConverter._haar_transform(col) for col in row_transformed.T]).T  # Columnas
            return col_transformed



    @staticmethod
    def apply_idwt(coeffs):
        """
        Apply Inverse Discrete Wavelet Transform (IDWT) to reconstruct data from DWT coefficients.
        :param coeffs: The list of wavelet coefficients (from apply_dwt).
        :return: The reconstructed data.
        """
        data = coeffs[-1]  # Comenzar con la aproximación más baja

        for transformed_data in reversed(coeffs[:-1]):
            # Reconstruir datos a partir de la aproximación y los detalles
            if data.ndim == 1:
                approx = data[:len(data) // 2]
                detail = data[len(data) // 2:]
                data = DWTConverter._haar_inverse_transform(approx, detail)
            elif data.ndim == 2:
                # Extraer aproximación y detalles de cada cuadrante
                rows, cols = transformed_data.shape
                approx = transformed_data[:rows // 2, :cols // 2]
                data = DWTConverter._haar_inverse_transform(approx)

        return data


    @staticmethod
    def _haar_inverse_transform(data):
        """
        Perform the inverse Haar transform to reconstruct data.
        Handles both 1D and 2D cases.
        :param data: The transformed data (1D or 2D).
        :return: The reconstructed original data.
        """
        data = np.array(data)

        if data.ndim == 1:
            # Reconstrucción 1D
            N = len(data) // 2
            approx = data[:N]
            detail = data[N:]
            reconstructed = np.zeros(2 * N)
            for i in range(N):
                reconstructed[2 * i] = approx[i] + detail[i]
                reconstructed[2 * i + 1] = approx[i] - detail[i]
            return reconstructed

        elif data.ndim == 2:
            # Reconstrucción 2D (columnas y luego filas)
            col_reconstructed = np.array([DWTConverter._haar_inverse_transform(col) for col in data.T]).T  # Columnas
            row_reconstructed = np.array([DWTConverter._haar_inverse_transform(row) for row in col_reconstructed])  # Filas
            return row_reconstructed
