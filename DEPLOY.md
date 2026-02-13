# Deploying SmartV2X-CP Ultra

## 1. Push to GitHub
Run the following command in your terminal to push the code to your repository:
```bash
git push -u origin main
```
*(If you see authentication errors, you may need to set up a Personal Access Token or SSH key for GitHub).*

## 2. Deploy to the Web (Free)

### Option A: Render (Recommended)
1. Create an account at [render.com](https://render.com).
2. Click **"New +"** -> **"Web Service"**.
3. Connect your GitHub repository (`monishav24/V2X`).
4. Render will automatically detect the `render.yaml` configuration.
5. Click **"Create Web Service"**.
   - The build might take 5-10 minutes.
   - Once done, you will get a public URL like `https://smartv2x-ultra.onrender.com`.

### Option B: Docker (Any Server)
To run the containerized application on any server with Docker installed:

1. **Build the image:**
   ```bash
   docker build -t smartv2x .
   ```

2. **Run the container:**
   ```bash
   docker run -p 3000:3000 -e JWT_SECRET=your_secret smartv2x
   ```
   Access at `http://localhost:3000`.

## Configuration
The `render.yaml` automatically sets up the environment. For manual deployment, ensure these environment variables are set:
- `JWT_SECRET`: A long random string.
- `DATABASE_URL`: Connection string for PostgreSQL (Render provides this automatically if you add a database).
- `REDIS_URL`: Connection string for Redis.
