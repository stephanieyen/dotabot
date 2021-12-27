import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

import requests 
from datetime import datetime, timezone, date, timedelta

class Support(LogicAdapter):
    """
    SUPPORTED QUERIES
        1. What are the currently supported DOTA deployments/cadences?

    REQUIREMENTS
        None

    SOURCES
        * Octantis: http://octantis.unx.sas.com:8080/promotions/ (Seshat API)
        * Code adapted from: https://gitlab.sas.com/mishel/octantis/-/blob/main/promoapp/views.py (get_supported_cadences(), promotions_view())
    """

    def __init__(self, chatbot, category="support", requirements="none (type/enter any letter to continue)"):
        super().__init__(chatbot, category, requirements)

    @staticmethod
    def get_supported_cadences(stage): 
        """
        Get all currently supported release cadence versions.

        :param (str) stage:                          promotion stage to search [testready, verified, prod, shipped)
        :return (list[str]) supported_cadence_names: list of cadence version names in the format <name>:<version> e.g. stable:2020.0.1
        """

        if stage == "production":
            stage = "prod"

        # Set up for Seshat API
        seshat_support_cadences_url = "http://reapi.sas.com:10001/pdsweb/Seshat/rest/v1/supportCadences"
        # Doesn't currently support filtering by "SUPPORTED" so search for cadence versions whose support ends after NOW
        time_str = datetime.now(timezone.utc).isoformat()
        seshat_params = LogicAdapter.seshat_params
        seshat_params['query'] = "AND(" f"GT(SUPPORT_CADENCE.END_AT,'{time_str}')," f"EQ(SUPPORT_CADENCE.PROMOTION_STAGE, '{stage}')" ")"
        seshat_headers = {"Accept": "application/vnd.sas.seshat.supportcadence.v1+json"}

        # Seshat API request
        resp = requests.get(seshat_support_cadences_url, params=seshat_params, headers=seshat_headers)
        supported_cadences = resp.json()
        print(supported_cadences)

        # Return name:version strings to represent cadence versions e.g. stable:2020.0.3
        supported_cadence_names = [c["name"] + ":" + c["version"] for c in supported_cadences]

        return supported_cadence_names
    
    def process(self, user_data): 
        # No requirements

        stage_cadences = {'TESTREADY': [], 
                          'VERIFIED': [],
                          'PROD': [],
                          'SHIPPED': []
                         }
        for stage in stage_cadences.keys():
            stage_cadences[stage] = Support.get_supported_cadences(stage)
        
        # Formatting
        stage_cadences = ",\n".join("{}: {}".format(*i) for i in stage_cadences.items()) 

        if stage_cadences != []:
            bot_response = stage_cadences
        else: 
            bot_response = "Sorry, I could not find the supported DOTA cadences. Please try again or refer to http://octantis.unx.sas.com:8080/promotions/."
        return bot_response