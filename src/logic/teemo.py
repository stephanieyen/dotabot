import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

import requests
from pprint import pprint

class Teemo(LogicAdapter):
    """
    SUPPORTED QUERIES
        1. Who are the test engineers for <DUName>?
    
    REQUIREMENTS
        * du_name (must start with quest_tools_)

    SOURCES
        * Teemo API
        * Code adapted from: https://gitlab.sas.com/mishel/test_coverage_worksheet/-/blob/main/excel_teemo_du_mapper.py
    """

    def __init__(self, chatbot, category="teemo", requirements="du_name (must start with quest_tools_)"):
        super().__init__(chatbot, category, requirements)


    def process(self, user_data): 
        du_name = user_data["du_name (must start with quest_tools_)"]

        # Set up Teemo API
        teemo_url = "http://teemo.sas.com:5002/testcontainers/get_registered_test_containers"

        # Teemo API request
        resp = requests.get(teemo_url)
        if resp.status_code == 200:
            teemo_results_json = resp.json()
        # pprint(teemo_results_json)

        # Parse Teemo test container output
        maintainers = {}
        for item in teemo_results_json['content']['results']:
            tmp_test_image_du_name = item.get("du_name", 'none')
            # tmp_test_targets = item.get("dus", 'none')

            if (tmp_test_image_du_name == du_name):
            # if ((tmp_test_image_du_name == du_name) or (du_name in tmp_test_targets)):
                maintainer = item.get("maintainer", "none")
                # Format maintainer (get rid of <> around email)
                maintainer = maintainer.replace(' <', ', ').replace('>', '')

                description = item.get("description", "none")
                maintainers[description] = maintainer

        if maintainers != {}:
            bot_response = str(maintainers)
        else:
            bot_response = "Sorry, I could not find your DU. Please try again or refer to Seshat/Teemo."

        
        return bot_response