# Phase 3: SonarCloud + Trivy Setup

Adds two gated stages to the Phase 2 pipeline: SonarCloud scans your source code right after
checkout, Trivy scans the built image right before it's pushed. Either can fail the build.

## 1. SonarCloud account + project

1. Go to https://sonarcloud.io → Log in with GitHub
2. "+" → Analyze new project → select your GitHub repo → Set Up
3. Choose **"With Jenkins"** setup (doesn't matter which you pick here, we're using our own Jenkinsfile stage anyway - just need the project created)
4. Note two values from the project setup screen:
   - **Organization Key** (e.g. `sunilkumar-org`)
   - **Project Key** (e.g. `sunilkumar_sample-python-app`)
5. Generate a token: your avatar (top right) → My Account → Security → Generate Token → name it `jenkins-token` → copy it immediately (shown once)

## 2. Fill in sonar-project.properties

Edit the file, replace both placeholders with your real values from step 1:
```
sonar.projectKey=sunilkumar_sample-python-app
sonar.organization=sunilkumar-org
```

## 3. Install Trivy on your Jenkins EC2

```bash
ssh -i <key>.pem ubuntu@<jenkins_ip>
sudo apt-get install -y wget apt-transport-https gnupg lsb-release
wget -qO - https://aquasecurity.github.io/trivy-repo/deb/public.key | gpg --dearmor | sudo tee /usr/share/keyrings/trivy.gpg > /dev/null
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb $(lsb_release -sc) main" | sudo tee -a /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install -y trivy

trivy --version   # confirm it worked
```

## 4. Add the SonarCloud token as a Jenkins credential

Jenkins → Manage Jenkins → Credentials → Add Credentials
- Kind: **Secret text**
- Secret: paste the token from step 1
- ID: `sonarcloud-token` (must match exactly - the Jenkinsfile references this)

## 5. Push and run

```bash
git add sonar-project.properties Jenkinsfile
git commit -m "Phase 3: add SonarCloud + Trivy scanning stages"
git push origin main
```

Trigger the pipeline. Watch the new stages:
- **SonarCloud Scan** — pulls the `sonarsource/sonar-scanner-cli` Docker image (first run only, slow), uploads your code for analysis. Check results at sonarcloud.io → your project.
- **Trivy Scan** — scans the freshly built image, prints a table of vulnerabilities by severity. If any HIGH or CRITICAL are found, this stage fails and the pipeline stops (nothing gets pushed or deployed).

## If Trivy fails your very first run

This is expected and okay — even minimal base images often have a few HIGH/CRITICAL CVEs.
Don't panic-fix everything at once. Options while you're getting this working initially:

- Temporarily loosen it to see the full report without blocking the pipeline:
  ```
  trivy image --severity HIGH,CRITICAL --exit-code 0 --format table ${IMAGE_NAME}:${IMAGE_TAG}
  ```
  (`--exit-code 0` = report only, never fails the build)
- Once you've reviewed what it found, switch back to `--exit-code 1` to make it a real gate
- A real fix for common base-image CVEs: use a newer/smaller base image (e.g.
  `python:3.12-slim` gets rebuilt regularly; pin to a recent digest, or try
  `python:3.12-alpine` for a smaller attack surface - though Alpine has its own trade-offs
  worth researching if you want to go deeper)

## What to say about this in an interview
- SonarCloud stage = static code analysis / SAST, gated on a Quality Gate before build
- Trivy stage = container image vulnerability scanning, gated on severity before push/deploy
- Both implement "shift-left security" - catching issues before they reach production, not after
