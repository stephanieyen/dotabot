import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

ORDER_DEF_FILE = os.path.join('src/storage', 'NA.yaml')
from yaml import safe_load

class Orderables(LogicAdapter):
    """
    SUPPORTED QUERIES
        1. Is my <sellableUnitName> in the DOTA NA (nearly all) order?
    
    REQUIREMENTS
        * sellable_unit_name

    SOURCES
        * NA.yaml (in dotabot/src/storage)
    """

    def __init__(self, chatbot, category="orderables", requirements="sellable_unit_name"):
        super().__init__(chatbot, category, requirements)

    @staticmethod
    def _get_order_def(order_def_file):
        with open(order_def_file, 'r') as yaml_file:
            parsed_yaml_file = safe_load(yaml_file)
        return set(parsed_yaml_file["orderables"])


    def process(self, user_data): 
        sellable_unit_name = user_data["sellable_unit_name"].upper() # Case-sensitive (must be upper)

        # Get orderables from NA.yaml
        orderables = Orderables._get_order_def(ORDER_DEF_FILE)

        # Search for specific sellable unit
        if sellable_unit_name in orderables: 
            bot_response = "Yes, found."
        else:
            bot_response = "No, not found."
        return bot_response
        


