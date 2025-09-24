# Beehive Placement Analyzer Deployment Guide

This guide provides step-by-step instructions for deploying the Beehive Placement Analyzer application on a VPS using Docker and Docker Compose.

## Prerequisites

- A VPS with a public IP address (e.g., `54.37.17.30`).
- SSH access to the VPS.
- A user with `sudo` privileges.

## Step 1: Install Docker and Docker Compose

First, you need to install Docker and Docker Compose on your VPS. Connect to your server via SSH and run the following commands:

### Install Docker
```bash
# Update the package list
sudo apt-get update

# Install prerequisites
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker's official GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add the Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

### Install Docker Compose
```bash
# Download the latest version of Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose

# Apply executable permissions to the binary
sudo chmod +x /usr/local/bin/docker-compose
```

### Add your user to the `docker` group (optional)
To run `docker` commands without `sudo`, add your user to the `docker` group:
```bash
sudo usermod -aG docker ${USER}
```
You will need to log out and log back in for this change to take effect.

## Step 2: Clone the Repository

Next, clone the application's repository to your VPS:
```bash
git clone <repository_url>
cd <repository_directory>
```
Replace `<repository_url>` with the actual URL of your Git repository and `<repository_directory>` with the name of the directory created by the clone command.

## Step 3: Configure the Firewall

Ensure that your VPS firewall allows traffic on port 80 (HTTP). If you are using `ufw`, you can enable it with the following command:
```bash
sudo ufw allow 80/tcp
```

## Step 4: Build and Run the Application

Now you are ready to build and run the application using Docker Compose. From the root of the project directory, run the following command:
```bash
docker-compose up --build -d
```
- `--build`: This flag tells Docker Compose to build the images before starting the containers.
- `-d`: This flag runs the containers in detached mode, so they will continue to run in the background.

## Step 5: Access the Application

Once the containers are running, you can access the application by navigating to your VPS's IP address in your web browser:
[http://54.37.17.30](http://54.37.17.30)

## Managing the Application

- **To stop the application:**
  ```bash
  docker-compose down
  ```
- **To view the logs:**
  ```bash
  docker-compose logs -f
  ```
- **To restart the application:**
  ```bash
  docker-compose restart
  ```

That's it! Your Beehive Placement Analyzer application is now deployed and accessible.