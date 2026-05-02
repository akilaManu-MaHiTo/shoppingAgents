from flask import Flask, render_template, request, jsonify
import json
from langgraph_flow import run_shopping_graph
import traceback

app = Flask(__name__)

@app.route('/')
def index():
    """Serve the chat UI"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Process user message through the shopping agents"""
    try:
        data = request.get_json()
        user_input = data.get('message', '').strip()
        
        if not user_input:
            return jsonify({
                'error': 'Empty message',
                'message': 'Please enter a search query'
            }), 400
        
        # Run the shopping graph
        state = run_shopping_graph(user_input)
        
        input_result = state.get("input_result", {})
        search_result = state.get("search_result", {})
        filter_result = state.get("filter_result", {})
        advisor_result = state.get("advisor_result", {})
        error = state.get("error")
        
        if error:
            return jsonify({
                'error': error,
                'message': 'An error occurred during processing'
            }), 500
        
        # Build comprehensive response
        response = {
            'user_input': user_input,
            'input_agent': {
                'product': input_result.get('product', 'unknown'),
                'category': input_result.get('category', 'unknown'),
                'price': input_result.get('price', 0),
                'specs': {
                    'CPU': input_result.get('CPU', ''),
                    'RAM': input_result.get('RAM', ''),
                    'Storage': input_result.get('Storage', ''),
                    'Storage Type': input_result.get('Storage Type', ''),
                    'GPU': input_result.get('GPU', ''),
                    'Generation': input_result.get('Generation', '')
                }
            },
            'search_agent': {
                'total_matches': search_result.get('totalMatches', 0),
                'result_mode': search_result.get('resultMode', 'closest_alternative'),
                'candidates_count': len(search_result.get('candidates', []))
            },
            'filter_agent': {
                'total_filtered': filter_result.get('totalFiltered', 0),
                'filter_mode': filter_result.get('filterMode', 'no_match'),
                'filters_applied': filter_result.get('filtersApplied', []),
                'rejected_count': filter_result.get('rejectedCount', 0),
                'duplicates_removed': filter_result.get('duplicatesRemoved', 0),
                'candidates': filter_result.get('filteredCandidates', [])
            },
            'advisor': {
                'fit_status': advisor_result.get('fit_status', 'no_fit'),
                'fit_score': advisor_result.get('fit_score', 0),
                'confidence': advisor_result.get('confidence', 'low'),
                'selected_product': advisor_result.get('selected_product'),
                'why_selected': advisor_result.get('why_selected', []),
                'mismatches': advisor_result.get('mismatches', []),
                'alternatives': advisor_result.get('alternatives', []),
                'improvement_suggestions': advisor_result.get('improvement_suggestions', []),
                'usage_tips': advisor_result.get('usage_tips', [])
            }
        }
        
        return jsonify(response)
    
    except Exception as e:
        print(f"Error: {traceback.format_exc()}")
        return jsonify({
            'error': str(e),
            'message': 'An unexpected error occurred'
        }), 500

@app.route('/api/history', methods=['GET'])
def get_history():
    """Fetch search history from input_history.json"""
    try:
        with open('input_history.json', 'r') as f:
            history = json.load(f)
        return jsonify({
            'status': 'success',
            'total_searches': len(history),
            'history': history
        })
    except FileNotFoundError:
        return jsonify({
            'status': 'success',
            'total_searches': 0,
            'history': [],
            'message': 'No history found'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'})

if __name__ == '__main__':
    print("🚀 Shopping Agents Chat UI Started")
    print("📱 Open http://localhost:5000 in your browser")
    app.run(debug=True, port=5000)
