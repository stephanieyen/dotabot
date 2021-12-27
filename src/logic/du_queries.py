import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

import requests 
from pprint import pprint

class DUQueries(LogicAdapter):
    """
    SUPPORTED QUERIES
        1. What version of <DUName> is at <promotionStage>?
        2. What lifecycle version of <DUName> is at <promotionStage>?
        3. When was <DUName> promoted to <promotionStage>?
    
    REQUIREMENTS
        * du_name
        * du_promotion_stage

    SOURCES
        * Seshat API
    """

    seshat_du_url = "http://reapi.sas.com:10001/pdsweb/Seshat/rest/v1/deployableUnits"

    def __init__(self, chatbot, category="du_queries", requirements="du_name, du_promotion_stage"):
        super().__init__(chatbot, category, requirements)

    @staticmethod
    def query_du(du_name, du_promotion_stage): 
        # Set up Seshat API
        seshat_params = LogicAdapter.seshat_params
        seshat_params["sortBy"] = 'DEPLOYABLE_UNIT.VERSION:ascending'
        seshat_params["start"] = 0
        seshat_params["subLimit"] = 1
        seshat_params["exclude"] = ['facets', 'relationships', 'components']
        seshat_params["query"] = 'AND( AND(EQ(DEPLOYABLE_UNIT.BUILD_LEVEL, "RELEASE"), ' + \
                                'EQ(DEPLOYABLE_UNIT.PROMOTION_STAGE, "{}"), '.format(du_promotion_stage) + \
                                'IN(DEPLOYABLE_UNIT.NAME, "{}")))'.format(du_name)

        # Seshat API request
        resp = requests.get(DUQueries.seshat_du_url, params=seshat_params)
        return resp

    def process(self, user_data): 
        du_name_input = user_data['du_name']
        du_promotion_stage_input = user_data['du_promotion_stage']

        # Default response
        bot_response = "Sorry, I could not find your DU. Please try again or refer to http://sww.sas.com/pdsweb/REDataPortal/."
        
        features = {'version': 'deployableUnitVersion', 
                    'promoted': 'promotedAt',
                    'lifecycle version': 'lifecycleVersion' }

        for feature_key in features:
            if feature_key in self.user_query:
                # Seshat API request
                resp = DUQueries.query_du(du_name_input, du_promotion_stage_input)
                if resp.status_code == 200 and resp.json:
                    if isinstance(resp.json(), list):
                        for du in resp.json():
                            # pprint(du)
                            # print(features[feature_key])
                            # Get specific DU feature
                            bot_response = feature_key.capitalize() + ": " + du.get(features[feature_key], "Not Found")

        return bot_response




