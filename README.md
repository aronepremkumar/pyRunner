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
