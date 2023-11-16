from playwright.sync_api import sync_playwright
from PIL import Image
import os
import time
import json
import sys

i = 0
telefon_numaralari = []
dbjson = 'static/users.json'

if len(sys.argv) > 1:
    veri = sys.argv[1]

def change_worker_status(user_id, new_status):
    with open(dbjson, 'r', encoding='utf-8') as users_file:
        users_data = json.load(users_file)
        users = users_data.get('users', [])
        for user in users:
            if user['id'] == int(user_id):
                user['worker'] = new_status
                break

    with open(dbjson, 'w', encoding='utf-8') as users_file:
        json.dump(users_data, users_file, indent=4)

def change_start_status(user_id):
    current_dateTime = datetime.now()
    listinfo = check_current(page, veri)
    with open(dbjson, 'r', encoding='utf-8') as users_file:
        users_data = json.load(users_file)
        users = users_data.get('users', [])
        for user in users:
            if user['id'] == int(user_id):
                user['last_startdate'] = current_dateTime
                user['last_sendl'] = listinfo[1]["name"]
                break

    with open(dbjson, 'w', encoding='utf-8') as users_file:
        json.dump(users_data, users_file, indent=4)

def change_qr_status(user_id, new_qr_status):
    with open(dbjson, 'r', encoding='utf-8') as users_file:
        users_data = json.load(users_file)
        users = users_data.get('users', [])
        for user in users:
            if user['id'] == int(user_id):
                user['qr_status'] = new_qr_status
                break

    with open(dbjson, 'w', encoding='utf-8') as users_file:
        json.dump(users_data, users_file, indent=4)

def get_user_data(user_id):
    with open(dbjson, 'r', encoding='utf-8') as users_file:
        users_data = json.load(users_file)
        users = users_data.get('users', [])
        for user in users:
            if user['id'] == int(user_id):
                print("data user bulundu")
                return user
    return None

def check_current(page, veri):
    bulundu = "none"
    while bulundu == "none":
        user_data = get_user_data(veri)
        for user_list in user_data["Lists"]:
            if user_list["current"] == "none" and bulundu == "none":
                print("current bulunamadı")
                time.sleep(3)
                user_data = get_user_data(veri)
            else:
                print("current bulundu")
                phone_numbers = user_list.get('phones', [])
                print(phone_numbers)
                bulundu = "yes"
        messagetext = user_data["last_messagetext"]
    return phone_numbers , user_list , messagetext

def send_message(page,phone_numbers,messagetext):
    print("firstload initiating")
    sendurl= "https://web.whatsapp.com/send?phone=+905393397509&text=message"
    time.sleep(120)
    for phone_number in phone_numbers:
        print(phone_number)
        sendurl= "https://web.whatsapp.com/send?phone=+90"+str(phone_number)+"&text="+messagetext
        print(sendurl)
        page.goto(sendurl)
        time.sleep(7)
        print("sayfa açıldı")
        page.keyboard.press('Enter')
        time.sleep(1)
        page.keyboard.press('Enter')
        time.sleep(1)

def wait_until_login(page):
    element = page.query_selector("._19vUU")
    while element is not None:
        time.sleep(1)
        element = page.query_selector("._19vUU")
    print("giriş yapıldı")

def main():
    try:
        user_data = get_user_data(veri)
        change_worker_status(veri,"active")
        print(user_data)
        with sync_playwright() as p:
            browser = p.firefox.launch()
            page = browser.new_page()
            page.goto("https://web.whatsapp.com/")
            print("browser open")
            time.sleep(5)
            page.screenshot(path="example.png")
            print("screenshot taken, waiting to process")
            qrcode = Image.open(r"example.png")
            qrcode = qrcode.convert('RGB')
            width, height = qrcode.size
            left = width/3*1.9
            top = height / 3
            right = width-width/7
            bottom = 2 * height / 2.5
            im1 = qrcode.crop((left, top, right, bottom))
            qrpath = "static"+user_data["qrpath"]
            print(qrpath)
            im1.save(qrpath)
            os.remove("example.png")
            change_qr_status(veri, "exist")
            print("qr saved, waiting for login...")
            wait_until_login(page)
            time.sleep(5)
            phone_numbers = check_current(page, veri)
            send_message(page,phone_numbers[0],phone_numbers[2])
            print("messages sent")
            change_qr_status(veri, "nexist")
            change_worker_status(veri,"deactive")
            os.remove(qrpath)
    except Exception as e:
        change_worker_status(veri,"deactive")
        try:
            os.remove(qrpath)
            change_qr_status(veri, "nexist")
        except:
            print("görsel silinemedi")
if __name__ == '__main__':
    main()