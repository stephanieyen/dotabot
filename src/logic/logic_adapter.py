import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from app import models

class LogicAdapter():
    """
    An abstract class that represents the interface that all logic adapters should implement.

    Each child class should describe the following in their docstring:
    * SUPPORTED QUERIES:    Possible queries that can be answered by the adapter.
    * REQUIREMENTS:         Inputs needed from the user to retrieve the data needed to answer the query.
    * SOURCES:              Databases, APIs, etc. from which data is retrieved to answer the query.
    * (optional) TESTS:     Example test cases or notes on performance.
    """

    # --- Common API info ---
    seshat_client_user_id = "DOTA automation"
    seshat_app_name = "DOTA automation"
    seshat_params = {
                "clientUserid": seshat_client_user_id, \
                "clientAppName": seshat_app_name, \
                "releaseContext": "viya_4.x", \
    }

    # --- Inherited or overriden by child classes ---
    def __init__(self, chatbot, category="", requirements=""):
        self.chatbot = chatbot
        self.user_query = "" 
        self.category = category
        self.requirements = requirements

    def can_process(self, query_id):
        """
        Checks if the logic adapter can process a given statement.
        Takes a query ID and sees if the query category matches the adapter category.
        
        :param (int) query_id: ID matched to one unique query  
        :return (bool):        True if the specific logic adapter can answer the query (based on query category).
                               Automatically False if the user doesn't input a supported query ID (either a string or out-of-bounds ID)
        """
        # Search database for a query by query_id (has to be int)
        try:
            query_id = int(query_id)
            db_query = models.get_query_by_id(query_id) 
            if db_query is not None and db_query.category == self.category: 
                # Store user query for this session
                self.user_query = db_query.query_text
                print("You chose:", str(db_query.id) + ". " + self.user_query)
                return True
        except ValueError or AttributeError:
            return False 

    def process(self, user_data):
        """
        Overridden by child classes.

        Reads user data and performs necessary queries/logic. 

        :param (dict) user_data:       Maps requirements for a query (keys) to input user data (values).
        :return (str) bot_response:    Response generated and returned by the bot.
        """
        bot_response = "" # Initially an empty string 
        raise self.AdapterMethodNotImplementedError()

    @property
    def class_name(self):
        """
        Return the name of the current logic adapter class.
        This is typically used for logging and debugging.
        """
        return self.__class__.__name__