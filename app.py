from flask import Flask, request, jsonify
from agent import deeper_research_topic

app = Flask(__name__)

@app.route('/research', methods=['POST'])
def research():
    data = request.get_json()
    if not data or 'station' not in data:
        return jsonify({"error": "Station not provided"}), 400

    station = data['station']
    result = deeper_research_topic(station)
    
    # The response from the agent is a dictionary, and the 'response' key contains the string to parse
    response_text = result.get('response', '')
    
    # Parsing the response string
    lines = response_text.strip().split('\n')
    incidents = []
    for line in lines:
        if line.startswith('LIST'):
            line = line[4:].strip()
        parts = line.split(',', 2)
        if len(parts) == 3:
            incidents.append({
                "description": parts[0].strip(),
                "time": parts[1].strip(),
                "station": parts[2].strip()
            })
            
    # Sorting the incidents by time (assuming a consistent time format)
    # This is a simple string sort. For more robust sorting, datetime parsing would be needed.
    sorted_incidents = sorted(incidents, key=lambda x: x['time'])
    
    # Replace the original response with the sorted list
    result['response'] = sorted_incidents
    
    return jsonify(result)

if __name__ == '__main__':
    # The host='0.0.0.0' makes the server accessible from your network.
    # The port can be changed if 5000 is in use.
    app.run(host='0.0.0.0', port=5000, debug=True)
