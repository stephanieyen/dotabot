import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

import requests 
from pprint import pprint # for testing

ORDER_DEF_FILE = os.path.join('src/storage', 'NA.yaml')
from yaml import safe_load

class Collection(LogicAdapter): 
    """
    SUPPORTED QUERIES
        1. What new DUs were introduced at <promotionStage> on <date>?
    
    REQUIREMENTS
        * promotion_stage
        * date (YYYY-MM-DD)

    SOURCES
        * Seshat API
        * Code adapted from: https://gitlab.sas.com/mishel/octantis/-/blob/main/flask_datarunner/seshatutils.py
    """

    def __init__(self, chatbot, category="collection", requirements="promotion_stage, date (YYYY-MM-DD)"):
        super().__init__(chatbot, category, requirements)
    
    @staticmethod
    def _get_order_def(order_def_file):
        """ 
        Return a list of orderables used in DOTA automation clusters.

        Uses a file from the DOTA cruise project: https://gitlab.sas.com/dota/cruise/-/blob/main/src/deployment_tooling/orders/NA.yaml 
        # Get the NA.yaml file from:
        # git clone git@gitlab.sas.com:dota/cruise.git
        """
        with open(order_def_file, 'r') as order_def:
            order_params = safe_load(order_def)
        return set(order_params["orderables"])

    @staticmethod
    def _get_na_orderables():
        """ 
        Query Seshat and return a list of NA orderables 
        """
        seshat_su_api = "http://reapi.sas.com:10001/pdsweb/Seshat/rest/v1/sellableUnits"
        seshat_mostat_api = "http://reapi.sas.com:10001/pdsweb/Seshat/rest/v1/traversals/mostSatisfying"
        
        # Set up for Seshat API
        headers = {
                    "Accept": "application/vnd.sas.seshat.sellable.unit.v3+json", 
                    "Cache-Control": "no-cache"
                }

        root_names = []
        du_list = []

        # Get orderables
        orderables = Collection._get_order_def(ORDER_DEF_FILE) 
        seshat_params = LogicAdapter.seshat_params
        seshat_params["scope"] = "viya4cd"
        seshat_params["buildType"] = "x64_oci_linux_2-docker"
        seshat_params["control"] = "IgnoreSUSURelationships"

        for orderable in orderables:
            seshat_params["include"] = ["scheduling", "legacy"]
            seshat_params["query"] = "EQ(SELLABLE_UNIT_LEGACY.TWELVE_BYTE," + orderable + ")"
            resp = requests.get(seshat_su_api, headers=headers, params=seshat_params)
            # pprint(resp.json())

            # Get SU root name and update root_names
            try:
                if isinstance(resp.json(), list):
                    root_names.append(resp.json()[0]["name"])
            except IndexError: 
                # resp.json() is empty []
                continue

        # Get all DUs for each SU root name
        # print(root_names)
        if root_names:
            headers = {
                "Accept": "application/vnd.sas.seshat.traversal.most.satisfying.v3+json",
                "Content-Type": "application/vnd.sas.seshat.traversal.most.satisfying.v2+json",
            }

            for root_name in root_names:
                print("Fetching DUs for SU:", root_name)
                seshat_params["entityType"] = "SellableUnit"
                seshat_params["buildLevel"] = "RELEASE"
                seshat_params["promotionStage"] = "testready"
                seshat_params["rootName"] = root_name

                resp = requests.get(seshat_mostat_api, headers=headers, params=seshat_params)

                if resp.status_code == 200 and resp.json().get("deployableUnits", None):
                    all_dus_list = resp.json().get("deployableUnits")
                    for du in all_dus_list:
                        print("DU found:", du.get("name"))
                        du_list.append(du.get("name"))

        print("Number of DUs found:", len(set(du_list))) # 221
        return set(du_list)

    @staticmethod
    def _get_seshat_promotions(image_list, promotion_stage, date):
        results = {} 

        # Set up for Seshat API
        seshat_url = "http://reapi.sas.com:10001/pdsweb/Seshat/rest/v1/deployableUnits" 
        seshat_headers = {
            "Accept": "application/vnd.sas.seshat.deployable.unit.v3+json"
        }
        seshat_params = LogicAdapter.seshat_params
        seshat_params["start"] = 0
        seshat_params["subLimit"] = 1
        seshat_params["exclude"] = ['facets', 'relationships', 'components']
        seshat_params["sortBy"] = 'DEPLOYABLE_UNIT.VERSION:ascending'

        # Fix DU image format for query (turns ['sas-', 'sas'] into "sas-", "sas-")
        parsed_images = ''
        for i in image_list:
            parsed_images = parsed_images + ('"%s",' % i)
        image_list = parsed_images.rstrip(',')
        seshat_params["query"] = """AND(AND (EQ(DEPLOYABLE_UNIT.DU_COMPONENT_TYPE, "PACKAGE_DOCKER"), '
                            'EQ(DEPLOYABLE_UNIT.BUILD_TYPE_DISPLAY_NAME, "x64_oci_linux_2-docker"), '
                            'EQ(DEPLOYABLE_UNIT.BUILD_LEVEL, "RELEASE"), EQ(DEPLOYABLE_UNIT.PROMOTION_STAGE, "{}")) , '
                            'IN(DEPLOYABLE_UNIT.NAME, {}))""".format(promotion_stage, image_list)

        # Seshat API request
        resp = requests.get(seshat_url, headers=seshat_headers, params=seshat_params)
        if resp.status_code == 200 and resp.json:
            if isinstance(resp.json(), list):
                for du in resp.json():
                    results[du['name']] = { 'timestamp': du.get('promotedAt', "Not Found"),
                                            'version': du.get('deployableUnitVersion', "Not Found"),
                                            'lifecycle': du.get('lifecycleVersion', 'Not Found')     }


        results_parsed = [] # List of DU names
        
        # Match date
        for du_name in results: 
            if(results[du_name]['timestamp'][0:10] == date):  # Date has 10 char: 2021-06-01
                results_parsed.append(du_name)

        if len(results_parsed) > 0:
            return results_parsed
        else:
            return "No promotion events found."

    def process(self, user_data): 
        promotion_stage = user_data['promotion_stage']
        date = user_data['date (YYYY-MM-DD)']
        
        # Feed in NA orderables
        # Returns DU (image) set - no duplicates
        na_order_dus = Collection._get_na_orderables()
        # print(na_order_dus)

        # Feed in DUs
        # Return DUs by promotion stage and date
        bot_response = Collection._get_seshat_promotions(na_order_dus, promotion_stage, date)

        return bot_response