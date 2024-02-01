from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
import paramiko
import logging
import requests
import re
import os
import yaml
from flask_session import Session

with open('config.yaml', 'r') as config_file:
    config = yaml.safe_load(config_file)

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)
app.secret_key = config.get('secret_key', os.urandom(16).hex())

# loggers setup
general_logger = logging.getLogger('general')
general_logger.setLevel(logging.INFO)
general_fh = logging.FileHandler('general.log')
general_formatter = logging.Formatter('%(asctime)s - %(message)s')
general_fh.setFormatter(general_formatter)
general_logger.addHandler(general_fh)

unblock_logger = logging.getLogger('unblock')
unblock_logger.setLevel(logging.INFO)
unblock_fh = logging.FileHandler('unblock.log')
unblock_formatter = logging.Formatter('%(asctime)s - %(message)s')
unblock_fh.setFormatter(unblock_formatter)
unblock_logger.addHandler(unblock_fh)

login_logger = logging.getLogger('login')
login_logger.setLevel(logging.INFO)
login_fh = logging.FileHandler('login.log')
login_formatter = logging.Formatter('%(asctime)s - %(message)s')
login_fh.setFormatter(login_formatter)
login_logger.addHandler(login_fh)

users = config.get('users', {})

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']  
        if users.get(username) == password:
            session['logged_in'] = True
            session['username'] = username
            flash('Logged in successfully.', 'success')
            login_logger.info(f"Successful login attempt for user: {username}")
            return redirect(url_for('blocked_ips'))
        else:
            flash('Invalid credentials.', 'danger')
            login_logger.warning(f"Failed login attempt for user: {username}")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    username = session.get('username')  
    session.clear()  
    flash('Logged out successfully.', 'success')
    
    login_logger.info(f"User {username} logged out.")
    
    return redirect(url_for('login'))


def ssh_execute_command(command):
    """
    Execute a command on the remote server via SSH and return the output and error.
    """
    ssh_client = paramiko.SSHClient()
    ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_client.connect(
        config['ssh']['hostname'],
        username=config['ssh']['username'],
        key_filename=config['ssh']['key_filename']
    )
    _, stdout, stderr = ssh_client.exec_command(command)
    output = stdout.read().decode()
    error = stderr.read().decode()
    ssh_client.close()
    return output, error

def get_remote_ipp():
    cmd = f'cat {config["ssh"]["ipp_file_path"]}'
    output, _ = ssh_execute_command(cmd)
    return output.split("\n")

@app.route("/blocked-ips", methods=["GET"])
@login_required
def blocked_ips():
    url = config['api']['url']
    auth_values = (config['api']['auth']['username'], config['api']['auth']['password'])
    response = requests.get(url, auth=auth_values, verify=False)
    
    if response.status_code != 200:
        return "Error fetching IPs from API.", 500
    
    json_response = response.json()
    ips_from_api = set([row["ip"] for row in json_response["rows"]])

    ipp_content = [line.strip().split(",") for line in get_remote_ipp() if line.strip()]
    matches = []
    for values in ipp_content:
        if len(values) == 3:
            username, ip, _ = values
            if ip in ips_from_api:
                matches.append([username, ip])
                ips_from_api.remove(ip)

    return render_template("display_ips.html", matches=matches, unmatched_ips=ips_from_api)

@app.route("/unblock", methods=["POST"])
@login_required
def unblock_user():
    username = request.form.get("username")
    quota = request.form.get("quota", "2000")
    cmd = f'sudo {config["commands"]["unblock_command"]} -u {username} -q {quota}'

    output, error = ssh_execute_command(cmd)

    if error:
        unblock_logger.error(f"Error executing command for user {username}: {error}")
        flash(f"Error unblocking user: {error}", 'danger')
    else:
        unblock_logger.info(f"Successfully unblocked user {username} with quota {quota}.")
        flash(f"Successfully unblocked user {username} with quota {quota}.", 'success')
    return redirect(url_for('blocked_ips'))

@app.route("/manual-unblock", methods=["GET", "POST"])
@login_required
def manual_unblock():
    logs = get_last_n_logs(10)  
    if request.method == "POST":
        username = request.form.get("username")
        quota = request.form.get("quota", "2000")
        cmd = f'sudo {config["commands"]["unblock_command"]} -u {username} -q {quota}'

        output, error = ssh_execute_command(cmd)

        if error:
            unblock_logger.error(f"Error executing manual unblock command for user {username}: {error}")
            flash(f"Error unblocking user manually: {error}", 'danger')
        else:
            unblock_logger.info(f"Successfully unblocked user {username} with quota {quota}.")
            flash(f"Successfully unblocked user {username} with quota {quota}.", 'success')
    return render_template("manual_unblock.html", logs=logs)


@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    if request.method == "POST":
        search_term = request.form.get("search_term")
        if not search_term:
            return "No input provided.", 400

        ipp_content = [line.strip().split(",") for line in get_remote_ipp() if line.strip()]
        matches = [line for line in ipp_content if search_term in line[0] or search_term in line[1]]

        return render_template("search.html", results=matches)

    return render_template("search.html", results=None)

def get_last_n_logs(n):
    logs = []
    try:
        with open("unblock.log", "r") as log_file:
            logs = log_file.readlines()[-n:]
    except FileNotFoundError:
        pass
    return logs

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)
