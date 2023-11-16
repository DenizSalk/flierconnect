import os
from flask import Flask, render_template, Response, request, redirect, url_for, session, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
from flask_login import current_user
import secrets
import subprocess
import json
import threading
from datetime import datetime
def generate_secret_key(length=24):
    return secrets.token_hex(length)

app = Flask(__name__)
secret_key = generate_secret_key()
app.secret_key = secret_key
login_manager = LoginManager()
login_manager.init_app(app)
dbjson = os.path.join(app.root_path, 'static', 'users.json')
process = None
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.request_loader
def load_user_from_request(request):
    username = request.form.get('username')
    password = request.form.get('password')
    if username and password:
        user_id = find_user_id(username, password)
        if user_id:
            user = User(user_id)
            return user
    return None

def find_user_id(username, password):
    with open(dbjson, 'r', encoding='utf-8') as users_file:
        users_data = json.load(users_file)
        users = users_data.get('users', [])
        for user in users:
            if user['username'] == username and user['password'] == password:
                return user['id']
    return None

def get_user_data(user_id):
    with open(dbjson, 'r', encoding='utf-8') as users_file:
        users_data = json.load(users_file)
        users = users_data.get('users', [])
        for user in users:
            if user['id'] == int(user_id):
                return user
    return None

def start_worker(user_id):
    global process
    process = subprocess.Popen(["python", "worker.py", user_id])

def stop_worker(user_id):
    global process
    return_code = process.terminate()
    user_data = get_user_data(user_id)
    os.remove("static"+user_data["qrpath"])
    with open(dbjson, 'r', encoding='utf-8') as users_file:
        users_data = json.load(users_file)
        users = users_data.get('users', [])
        for user in users:
            if user['id'] == int(user_id):
                user['worker'] = "deactive"
                user['qr_status'] = "nexist"
                user_lists = user.get('Lists', [])
                for user_list in user_lists:
                        user_list['current'] = 'none'
                break
    with open(dbjson, 'w', encoding='utf-8') as users_file:
        json.dump(users_data, users_file, indent=4)
    session.pop('from_calistir', None)

@login_manager.user_loader
def load_user(user_id):
    user = User(user_id)
    return user

@app.route("/")
def mainpage():
    return  render_template("index.html")

@app.route('/login')
def loginr():
    if current_user.is_authenticated:
        return redirect("/dashboard")
    return render_template("login.html")

@app.route('/auth', methods=['POST'])
def auth():
    # Kullanıcıyı oturum açtırın.
    username = request.form['username']
    password = request.form['password']
    user_id = find_user_id(username, password)
    if user_id:
        user = User(user_id)
        login_user(user)
        return redirect("/dashboard")
    return redirect("/login")

@login_required
@app.route("/dashboard")
def dashboard():
    if current_user.is_authenticated:
        user_id = current_user.id
        user_data = get_user_data(user_id)
        from_calistir = session.get('from_calistir', False)
        if user_data:
            if from_calistir:
                return render_template("dashboard.html", user_data=user_data, is_from_calistir=True)
            else:
                return render_template("dashboard.html", user_data=user_data, is_from_calistir=False)
        else:
            return "User not found or an error occurred while fetching user data."
    return render_template("login.html")

@app.route('/handlelist', methods=['GET', 'POST'])
def handlelist():
    user_id = current_user.id
    try:
        listaction = request.args.get('action')
        listname = request.args.get('listname')
        phonenumbers = request.args.get('phonenumbers')

        with open(dbjson, 'r', encoding='utf-8') as users_file:
            users_data = json.load(users_file)
            users = users_data.get('users', [])
            for user in users:
                if user['id'] == int(user_id):
                    user_lists = user.get('Lists', [])

                    if listaction == "delete":
                        # Create a copy of the list to avoid modification issues
                        user_lists_copy = user_lists[:]
                        for user_list in user_lists_copy:
                            if user_list['name'] == listname:
                                print(user_list)  # Print user_list before removing it
                                user_lists.remove(user_list)
                                break
                        break  # Break out of the outer loop once the list is modified

                    elif listaction == "add":
                        # Check if the list with the specified name already exists
                        existing_list = next((lst for lst in user_lists if lst['name'] == listname), None)
                        if existing_list is None:
                            # Add a new list to the user's data
                            new_list = {'name': listname, 'items': []}

                            # Parse phone numbers from the textarea
                            phone_numbers = [number.strip() for number in phonenumbers.split('\n') if number.strip()]
                            new_list['phones'] = phone_numbers

                            current_date = datetime.now().strftime("%Y-%m-%d")
                            new_list['listdatedate'] = current_date

                            user_lists.append(new_list)
                            print(f"Added new list: {new_list}")
                            break  # Break out of the outer loop after adding the list

        # Save the modified user data back to the file
        with open(dbjson, 'w', encoding='utf-8') as users_file:
            json.dump(users_data, users_file, indent=4)

    except Exception as e:
        print(f"An error occurred: {e}")

    return redirect("/dashboard")

@app.route('/send', methods=['GET', 'POST'])
@login_required
def set_current_list():
    user_id = current_user.id
    try:
        list_name = request.form['currentlist']
        print("before message")
        last_messagetext = request.form['last_messagetext']
        print(last_messagetext)
        print(list_name)
        with open(dbjson, 'r', encoding='utf-8') as users_file:
            users_data = json.load(users_file)
            users = users_data.get('users', [])
            for user in users:
                if user['id'] == int(user_id):
                    user['last_messagetext'] = last_messagetext
                    user_lists = user.get('Lists', [])
                    for user_list in user_lists:
                        if user_list['name'] == list_name:
                            user_list['current'] = 'yes'
                        else:
                            user_list['current'] = 'none'

        with open(dbjson, 'w', encoding='utf-8') as users_file:
            json.dump(users_data, users_file, indent=4, ensure_ascii=False)

    except Exception as e:
        print(f"An error occurred: {e}")

    return redirect("/dashboard")

@login_required
@app.route('/logout')
def logout():
    user_id = current_user.id
    try:
        stop_worker(user_id)
    except:
        pass
    logout_user()
    session.pop('from_calistir', None)
    return redirect('/login')

@login_required
@app.route('/worker', methods=['POST'])
def worker():
    engine = request.form['engine']
    if engine == "start":
        user_id = current_user.id
        start_thread = threading.Thread(target=start_worker, args=(user_id,))
        start_thread.start()
        session['from_calistir'] = True
        return redirect(url_for('dashboard'))
    if engine == "stop":
        user_id = current_user.id
        stop_worker(user_id)
        return redirect(url_for('dashboard'))
    else:
        return "hata oluştu"

if __name__ == '__main__':
    app.run()