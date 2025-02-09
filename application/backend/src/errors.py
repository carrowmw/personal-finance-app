# application/backend/src/utils.py

import json

def format_error(e):
    response = json.loads(e.body)
    return {
        "error": {
            "status_code": e.status,
            "display_message": response["error_message"],
            "error_code": response["error_code"],
            "error_type": response["error_type"],
        }
    }
