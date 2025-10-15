#!/usr/bin/env python3
"""
建立測試用圖片
如果沒有真實圖片，可以用此腳本生成測試用的佔位圖片
"""
from PIL import Image, ImageDraw, ImageFont
import os

def create_test_image(filename, text, color):
    """建立測試圖片"""
    # 建立 800x600 的圖片
    img = Image.new('RGB', (800, 600), color=color)
    draw = ImageDraw.Draw(img)
    
    # 在圖片中央加入文字
    try:
        # 嘗試使用系統字體
        font = ImageFont.truetype("/System/Library/Fonts/PingFang.ttc", 40)
    except:
        # 如果找不到字體，使用預設字體
        font = ImageFont.load_default()
    
    # 計算文字位置（置中）
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    position = ((800 - text_width) // 2, (600 - text_height) // 2)
    
    # 繪製文字
    draw.text(position, text, fill='white', font=font)
    
    # 儲存圖片
    output_path = os.path.join('test_images', filename)
    img.save(output_path, 'JPEG', quality=85)
    print(f"✅ 已建立: {output_path}")

def main():
    print("🖼️  建立測試圖片...")
    
    # 確保資料夾存在
    os.makedirs('test_images', exist_ok=True)
    
    # 建立三張測試圖片
    create_test_image('damage_before.jpg', '災前照片\nBefore Damage', '#4A90E2')
    create_test_image('damage_after.jpg', '災後照片\nAfter Damage', '#E24A4A')
    create_test_image('inspection.jpg', '現場勘查照片\nInspection Photo', '#50C878')
    
    print("\n✨ 測試圖片建立完成！")
    print("📁 位置: ./test_images/")
    print("\n您現在可以使用這些圖片進行 API 測試")
    print("或將它們替換為真實的災損照片")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ 錯誤: {e}")
        print("\n請確認已安裝 Pillow:")
        print("pip install pillow")

