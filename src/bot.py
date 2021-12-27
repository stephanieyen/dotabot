import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from app import models

class Bot(object):
    """
    A chat bot.
    """

    def __init__(self, bot_name, user_name=None, **kwargs):
        self.bot_name = bot_name            
        self.user_name = user_name          

        # -- Set up logic adapters --
        logic_adapters = kwargs.get('logic_adapters') 
        self.logic_adapters = [] # List of logic adapter objects

        import importlib
        for adapter_module_path in logic_adapters: 
            module = importlib.import_module(adapter_module_path) # Import adapter module based on specified relative path

            # Parse module path to get correct class name (e.g., du_queries --> DUQueries)
            class_name = adapter_module_path.split('.')[2] 
            parsed_class_name = class_name.replace('_', '')
            for obj in dir(module): 
                if parsed_class_name.lower() == obj.lower(): # Case-insensitive
                    class_name = obj 

            logic_adapter_class = getattr(module, class_name)   # Get class name attribute
            logic_adapter = logic_adapter_class(self)           # Create a new logic adapter object
            self.logic_adapters.append(logic_adapter)
    
    def specify_requirements(self, query_id):
        try:
            query_id = int(query_id)
            db_query = models.get_query_by_id(query_id) 
            if db_query is not None: 
                for adapter in self.logic_adapters:
                    if adapter.can_process(query_id):
                        return adapter.requirements
        except:
            return "Sorry, that query is not supported. Try again with a supported query ID."

        # All logic adapters return False
        return "Sorry, that query is not supported. Try again with a supported query ID."
        

    def answer(self, mapped_req_values=None): 
        """
        Return the bot's response based on the input.

        :param statement: input statement
        :type statement: string

        :returns: bot's response statement
        :rtype: string
        """
        bot_response = "Response not found." # Default

        # General case: user input is a number corresponding to a question
        for adapter in self.logic_adapters: 
            if adapter.can_process(mapped_req_values['id']):
                bot_response = adapter.process(mapped_req_values) 
            # else:
            #     print(str(adapter) + " can not process")
        
        return bot_response