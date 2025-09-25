# Beehive Placement Analyzer Deployment Guide

This guide provides step-by-step instructions for deploying the Beehive Placement Analyzer application on a server using Docker and Docker Compose.

## Prerequisites

- A server with a public IP address (e.g., `54.37.17.30`).
- SSH access to the server.
- A user with `sudo` privileges.
- Docker and Docker Compose installed. If you need to install them, see the "Installing Docker and Docker Compose" section at the end of this guide.

## Deployment

### Step 1: Clone the Repository
Clone the application's repository to your server:
```bash
git clone <repository_url>
cd <repository_directory>
```
*Replace `<repository_url>` and `<repository_directory>` with your actual repository details.*

### Step 2: Build and Run the Application
From the root of the project directory, run the following command:
```bash
docker-compose up --build -d
```
This command builds the Docker images and starts the application containers in the background. The application will be running on port `8080`.

### Step 3: Access the Application
You can now access the application directly by navigating to your server's IP address and port `8080` in your web browser:
**http://54.37.17.30:8080**

## Integrating with Your Existing Nginx (for n8n)

You mentioned you are running `n8n` on the same server, which uses a global Nginx server. To make the Beekeeper app accessible on the standard port 80/443 (e.g., at a path like `https://54.37.17.30/beekeeper`), you should modify your **existing global Nginx configuration** to act as a reverse proxy.

**1. Edit your existing Nginx configuration file:**
Open the configuration file that handles your `n8n` application. This is likely located at `/etc/nginx/sites-available/n8n`.
```bash
sudo nano /etc/nginx/sites-available/n8n
```

**2. Add a new `location` block for the Beekeeper app:**
Inside the `server { listen 443 ssl; ... }` block, after the existing `location / { ... }` block for `n8n`, add the following new block.

```nginx
    # Add this new block for the Beekeeper App
    location /beekeeper/ {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
```
*Save and close the file (`Ctrl+X`, `Y`, `Enter`).*

**3. Test and restart your global Nginx:**
```bash
sudo nginx -t
sudo systemctl restart nginx
```

After this, you should be able to access the Beekeeper application at **https://54.37.17.30/beekeeper/**.

---

## Managing the Application

- **To stop the application:** `docker-compose down`
- **To view logs:** `docker-compose logs -f`
- **To restart:** `docker-compose restart`

---

## Appendix: Installing Docker and Docker Compose

If you don't have Docker and Docker Compose installed, follow these steps.

**Install Docker:**
```bash
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io
```

**Install Docker Compose:**
```bash
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**Add user to Docker group (optional, avoids using `sudo` for Docker commands):**
```bash
sudo usermod -aG docker ${USER}
```
*(You will need to log out and back in for this to take effect.)*