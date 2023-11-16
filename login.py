import time
from playwright.sync_api import sync_playwright
from PIL import Image
import os

with sync_playwright() as p:
    browser = p.firefox.launch()
    context = browser.new_context()
    page = browser.new_page()
    page.goto("https://web.whatsapp.com/")
    time.sleep(5)
    page.screenshot(path="example.png")
    qrcode = Image.open(r"example.png")
    qrcode = qrcode.convert('RGB')
    width, height = qrcode.size
    left = width/3*1.9
    top = height / 3
    right = width-width/7
    bottom = 2 * height / 2.5
    im1 = qrcode.crop((left, top, right, bottom))
    im1.save("static/cropped_image.jpg")
    os.remove("example.png")
    time.sleep(20)
    cookies = context.cookies()
    time.sleep(5)
    browser.close()