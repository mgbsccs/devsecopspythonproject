# devsecopspipeline
a sample python project
---

# Project Documentation

## Overview

This project is a web application built using the Flask framework in Python. It demonstrates user authentication, session management, and interaction with external systems via SSH and HTTP requests. The application allows users to log in/out, view blocked IP addresses, unblock users, and perform searches on log data.

## Setup

### Prerequisites

- Python 3.6+
- Flask
- Paramiko
- Requests
- YAML
- Flask-Session

### Installation

1. Clone the repository:
   ```
   git clone <repository_url>
   ```
2. Navigate to the project directory:
   ```
   cd <project_directory>
   ```
3. Install the required Python packages:
   ```
   pip install -r requirements.txt
   ```

### Configuration

- Copy `config.yaml.template` to `config.yaml`.
- Fill in your configurations such as `secret_key`, SSH details, API credentials, and user credentials in `config.yaml`.

## Running the Application

1. Start the app:
```
docker build --no-cache -t show-blocked-app . && docker run -d -p 5002:5002 show-blocked-app
```
2. Access the web application at `http://localhost:5002`.

## Features

### User Authentication

- Users can log in to access protected routes.
- Sessions are managed to keep track of logged-in state.

### Viewing Blocked IPs

- Fetches blocked IP addresses from an external API and an SSH-connected server.
- Displays matching and unmatched IP addresses.

### Unblock Users

- Provides functionality to unblock users via a web interface.
- Supports manual unblocking with customizable quotas.

### Logging

- Uses Python's logging module to log general events, login attempts, and unblocking actions.

### Secure Configuration

- Utilizes an external YAML configuration file for sensitive and variable data.
