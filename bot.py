# imports

from flask import Flask, request
from werkzeug.exceptions import BadRequest

# Initialize Flask app
app = Flask(__name__)

# Handle all requests
@app.route('/webhook', methods=['POST'])
def handle():
    # Parse JSON payload
    data = request.get_json()
    if data is None:
        raise BadRequest('No JSON payload found')

    # Process the data
    # Your processing logic here
    print(data)

    return "OK"
