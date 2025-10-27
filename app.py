
from flask import Flask
import os

app = Flask("PyRunner")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)