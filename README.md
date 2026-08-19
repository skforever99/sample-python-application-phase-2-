# Phase 2: Sample App - Build, Push, Deploy

A small Flask app, packaged into Docker, pushed to Docker Hub, deployed onto the k3s cluster from Phase 1.

## Files
- `app.py` / `requirements.txt` — the Flask app
- `Dockerfile` — packages it into an image
- `deployment.yaml` / `service.yaml` — K8s manifests (Service is NodePort 30080, matches the port range already open in Phase 1's security group)
- `Jenkinsfile` — build image → push to Docker Hub → deploy to k3s

## 1. Test the app locally (optional but quick)
```bash
pip install -r requirements.txt
python app.py
# visit http://localhost:5000 and http://localhost:5000/health
```

## 2. Test the Docker image locally (optional)
```bash
docker build -t sample-python-app:test .
docker run -p 5000:5000 sample-python-app:test
# visit http://localhost:5000
```

## 3. Set your Docker Hub username

Edit `Jenkinsfile`, replace `DOCKERHUB_USERNAME_PLACEHOLDER` with your actual Docker Hub username.

## 4. Add credentials in Jenkins (two of them)

### Docker Hub credentials
1. Docker Hub → Account Settings → Security → New Access Token (don't use your real password)
2. Jenkins → Manage Jenkins → Credentials → (global) → Add Credentials
3. Kind: **Username with password**
4. Username: your Docker Hub username, Password: the access token
5. ID: `dockerhub-creds` (must match exactly — the Jenkinsfile references this ID)

### k3s kubeconfig (so Jenkins can deploy to the cluster)
1. On your Mac (or wherever you have it), pull the kubeconfig from your current k3s node:
   ```bash
   scp -i <your-key>.pem ubuntu@<k3s_node_ip>:/etc/rancher/k3s/k3s.yaml ./kubeconfig.yaml
   sed -i '' "s/127.0.0.1/<k3s_node_ip>/" kubeconfig.yaml   # Mac sed syntax
   ```
2. Jenkins → Manage Jenkins → Credentials → Add Credentials
3. Kind: **Secret file**
4. Upload `kubeconfig.yaml`
5. ID: `k3s-kubeconfig` (must match exactly)

**Important:** if you destroy and recreate the k3s cluster (Phase 1's `DESTROY` pipeline), the node gets a new IP — you'll need to re-fetch the kubeconfig and re-upload it here, since the old one points at an IP that no longer exists. This is the one manual step in an otherwise automated flow; worth calling out if it comes up in review, since a production setup would use a static/elastic IP or a service mesh to avoid this.

## 5. Also needed on the Jenkins EC2
Docker must be installed there (so the `docker build`/`push` stages work), and `kubectl` (so the deploy stage works). If you didn't do this during Phase 1:
```bash
# Docker
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins

# kubectl
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## 6. Push this project and create the Jenkins job
Same pattern as Phase 1 — push to GitHub, create a new Pipeline job, "Pipeline script from SCM", Script Path = `Jenkinsfile`.

## 7. Run it
Build Now. Watch: Checkout → Build → Push → Deploy. Once it succeeds:
```bash
curl http://<k3s_node_ip>:30080
curl http://<k3s_node_ip>:30080/health
```

## Cost/state note
Make sure the k3s cluster from Phase 1 is actually running (not destroyed) before triggering this pipeline — the Deploy stage needs a live cluster to talk to.
