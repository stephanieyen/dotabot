import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.bot import Bot

# -- Initialize bot with logic adapters --
dotabot = Bot(
                'Test Bot', 
                logic_adapters=[
                    # Add new logic adapters here
                    'src.logic.collection',
                    'src.logic.confluence',
                    'src.logic.du_queries', 
                    'src.logic.orderables',
                    'src.logic.scribe',
                    'src.logic.support', 
                    'src.logic.teemo',
                    'src.logic.time'
                ]
)

# -- Import and config section --

from flask import jsonify, request, render_template
from app import app, db, models
from app.models import Queries
app.config['DEBUG'] = True

# Create a shell context that adds the database instance + model(s) to the shell session
# when running <flask shell> command
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'Queries': Queries}

# -- Routes section --

@app.route('/')
def index():
    queries = models.get_all_query_text() # List of all queries that are currently supported (from Queries database)
    return render_template('index.html', queries=queries)

@app.route('/question', methods=['GET'])
def question():
    """ 
    User specifies the question they would like answered via query ID.
    Bot specifies the requirements (data needed to answer the question). 
    """
    query_id = request.args.get('id')
    requirements = dotabot.specify_requirements(query_id) 
    return requirements 

# post to get multiple things
@app.route('/answer', methods=['POST'])
def answer():
    """
    User has provided their data for the requirements.
    Bot provides the final answer to the user's specified question.
    """
    mapped_req_values = request.get_json() # Parse data as JSON object
    answer = dotabot.answer(mapped_req_values) 
    return answer 

if __name__ == "__main__":
    pass
    # app.run(debug=True)