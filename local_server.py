from flask import Flask, request, jsonify
import json
import uuid
from datetime import datetime
from lambda_function import lambda_handler

app = Flask(__name__)

@app.route('/', methods=['GET'])
def api_info():
    """API information endpoint."""
    event = {'httpMethod': 'GET'}
    response = lambda_handler(event, None)
    return jsonify(json.loads(response['body'])), response['statusCode']

@app.route('/process-homework', methods=['POST', 'OPTIONS'])
def process_homework():
    """Main homework processing endpoint."""
    
    if request.method == 'OPTIONS':
        event = {'httpMethod': 'OPTIONS'}
    else:
        event = {
            'httpMethod': 'POST',
            'body': json.dumps(request.get_json() if request.is_json else {}),
            'requestContext': {'requestId': f'local-{uuid.uuid4()}'}
        }
    
    # Call Lambda handler
    response = lambda_handler(event, None)
    
    # Return Flask response with proper headers
    flask_response = jsonify(json.loads(response['body']))
    flask_response.status_code = response['statusCode']
    
    # Add CORS headers
    for header, value in response.get('headers', {}).items():
        flask_response.headers[header] = value
    
    return flask_response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Smart Homework Assistant MVP',
        'mode': 'local_development',
        'timestamp': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    print("🚀 Starting Smart Homework Assistant Local Server...")
    print("📚 Access API at: http://localhost:5000")
    print("🔍 Health check: http://localhost:5000/health")
    print("💡 Main endpoint: http://localhost:5000/process-homework")
    app.run(debug=True, host='0.0.0.0', port=5000)