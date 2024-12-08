import cv2
import numpy as np
from typing import Tuple

class ImagePreprocessor:
    @staticmethod
    async def enhance_image(image: np.ndarray) -> np.ndarray:
        # 降噪
        denoised = cv2.fastNlMeansDenoisingColored(image, None, 10, 10, 7, 21)
        # 对比度增强
        lab = cv2.cvtColor(denoised, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        cl = clahe.apply(l)
        enhanced = cv2.merge((cl,a,b))
        return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
    
    @staticmethod
    async def deskew(image: np.ndarray) -> Tuple[np.ndarray, float]:
        # 灰度转换
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150, apertureSize=3)
        # 霍夫变换
        lines = cv2.HoughLines(edges, 1, np.pi/180, 200)
        
        if lines is not None:
            angle = 0
            for rho, theta in lines[0]:
                angle = theta * 180 / np.pi
                if angle < 45:
                    angle = angle
                elif angle < 90:
                    angle = angle - 90
                
            # 旋转校正
            (h, w) = image.shape[:2]
            center = (w // 2, h // 2)
            M = cv2.getRotationMatrix2D(center, angle, 1.0)
            rotated = cv2.warpAffine(image, M, (w, h), 
                                   flags=cv2.INTER_CUBIC, 
                                   borderMode=cv2.BORDER_REPLICATE)
            return rotated, angle
        
        return image, 0.0