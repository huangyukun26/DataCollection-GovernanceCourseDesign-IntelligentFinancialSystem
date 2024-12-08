import cv2
import numpy as np
from pathlib import Path

def create_sample_invoice():
    """创建一个测试用的发票图片"""
    # 创建空白图像
    img = np.ones((1200, 1000, 3), dtype=np.uint8) * 255
    
    # 添加发票内容
    text_lines = [
        ("增值税专用发票", 60, (200, 100), 3),
        ("发票号码：12345678", 40, (100, 200), 2),
        ("开票日期：2024年3月14日", 40, (100, 300), 2),
        ("销售方名称：测试科技有限公司", 40, (100, 400), 2),
        ("销售方地址：北京市海淀区", 40, (100, 500), 2),
        ("购买方名称：示例企业有限公司", 40, (100, 600), 2),
        ("购买方地址：上海市浦东新区", 40, (100, 700), 2),
        ("金额：¥10,000.00", 40, (100, 800), 2),
        ("税额：¥1,300.00", 40, (100, 900), 2)
    ]
    
    # 设置字体
    font = cv2.FONT_HERSHEY_SIMPLEX
    color = (0, 0, 0)
    
    # 写入文本
    for text, font_scale, position, thickness in text_lines:
        cv2.putText(img, text, position, font, font_scale/30, color, thickness)
    
    # 添加表格线
    cv2.rectangle(img, (50, 50), (950, 950), (0, 0, 0), 3)
    
    # 保存图像
    output_dir = Path(__file__).parent / "test_data" / "invoice"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    cv2.imwrite(str(output_dir / "sample_invoice.jpg"), img)
    print(f"Created sample invoice at: {output_dir / 'sample_invoice.jpg'}")

if __name__ == "__main__":
    create_sample_invoice() 