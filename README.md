# PyRunner
# Python Execution Service (Flask + nsjail)

This service exposes a single endpoint:

`POST /execute` with JSON `{ "script": "<python code containing def main(): ...>" }`

Response:
```json
{
  "result": ...,   // JSON-serializable return value from main()
  "stdout": "..."  // text printed by the script during execution
}
```

🧱 Build and Run Locally
1️⃣ Build the Docker image
docker build -t pyrunner:latest .

2️⃣ Run the container
docker run --rm -p 8080:8080 pyrunner:latest
