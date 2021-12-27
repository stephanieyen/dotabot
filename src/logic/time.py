import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

import requests 
from pprint import pprint

class Time(LogicAdapter):
    """
    SUPPORTED QUERIES
        1. How long did it take <duName> to promote from <promotionStage1> to <promotionStage2>? (e.g., TESTREADY to PROD)

    REQUIREMENTS
        * du_name
        * first_promotion_stage
        * second_promotion_stage
        * num_last_promotions_to_analyze
    
    SOURCES
        * Seshat API
    """

    seshat_du_url = "http://reapi.sas.com:10001/pdsweb/Seshat/rest/v1/deployableUnits"

    def __init__(self, chatbot, category="time", requirements="du_name, first_promotion_stage, second_promotion_stage, num_last_promotions_to_analyze (used to calculate an average time)"):
        super().__init__(chatbot, category, requirements)

    @staticmethod
    def get_du_versions_list(du_name): 
        """ 
        Returns a list of DU versions given the DU name via Seshat query.

        :param (str) du_name:               DU name as specified by user. 
        :return (list[str]) du_versions:    List of past versions for the given DU, with duplicates removed.
                                            Ordered from most recent to least recent.
        """ 

        # Set up for Seshat API
        seshat_params = LogicAdapter.seshat_params 
        seshat_params['sortBy'] = 'DEPLOYABLE_UNIT.VERSION:descending'
        seshat_params["query"] = 'AND( AND(EQ(DEPLOYABLE_UNIT.BUILD_LEVEL, "RELEASE"), ' + \
                            'IN(DEPLOYABLE_UNIT.NAME, "{}")))'.format(du_name) \
            
        # API request
        resp = requests.get(Time.seshat_du_url, params=seshat_params)
        
        # Add DU versions to a list
        du_versions = []
        if resp.status_code == 200 and resp.json:
            if isinstance(resp.json(), list):
                for du in resp.json():
                    du_versions.append(du.get('deployableUnitVersion', "Not Found"))

        # Use OrderedDict to remove duplicates (due to multiple DU data entries for the same version at diff promo stages)
        from collections import OrderedDict 
        du_versions = list(OrderedDict.fromkeys(du_versions))
        return du_versions
    
    @staticmethod
    def get_promotedAt_specVersion(du_name, du_version, promotion_stage): 
        """
        Gets the time that a specific version of a DU was promoted to a specific promotion stage via Seshat query.

        :param (str) du_name:           DU name as specified by user.
        :param (str) du_version:        DU version that is being evaluated.
        :param (str) promotion_stage:   Promotion stage as specified by user. (TESTREADY, VERIFIED, PROD, SHIPPED)
        :return (str):                  Time that the DU was promoted to promotion_stage.
        """

        # Set up for Seshat API
        seshat_params = LogicAdapter.seshat_params
        seshat_params["query"] = 'AND( AND(EQ(DEPLOYABLE_UNIT.BUILD_LEVEL, "RELEASE"), ' + \
                            'EQ(DEPLOYABLE_UNIT.VERSION, "{}"), '.format(du_version) + \
                            'EQ(DEPLOYABLE_UNIT.PROMOTION_STAGE, "{}"), '.format(promotion_stage) + \
                            'IN(DEPLOYABLE_UNIT.NAME, "{}")))'.format(du_name) \

        # API request
        resp = requests.get(Time.seshat_du_url, params=seshat_params)

        # Find time promoted to given stage
        if resp.status_code == 200 and resp.json:
                if isinstance(resp.json(), list):
                    for du in resp.json():
                        return(du.get('promotedAt', "Not Found"))

    @staticmethod
    def validate(du_name, du_version, first_promotion_stage, second_promotion_stage):
        """
        Validates that a specific version of a DU has promotion times/data for both stages specified by the user.
        Promotion data might not exist if a version of the DU has not been promoted to that stage yet.

        :param (str) du_name:                  DU name as specified by user.
        :param (str) du_version:               DU version that is being evaluated.
        :param (str) first_promotion_stage:    First promo stage as specified by user ("from"). (TESTREADY, VERIFIED, PROD, SHIPPED)
        :param (str) second_promotion_stage:   Second promo stage as specified by user ("to"). (TESTREADY, VERIFIED, PROD, SHIPPED)
        :return (tuple):    index 0 (bool):    True is promotion data is found/non-None.
                            index 1 (str):     Promotion time for first stage.
                            index 2 (str):     Promotion time for second stage.
        """
        first_time = Time.get_promotedAt_specVersion(du_name, du_version, first_promotion_stage)
        second_time = Time.get_promotedAt_specVersion(du_name, du_version, second_promotion_stage)
        if (first_time is not None and second_time is not None):
            return True, first_time, second_time
        else: 
            return False, first_time, second_time
    
    @staticmethod
    def time_diff(first_time, second_time): 
        """
        Finds the difference between two times in timedelta format.

        :param (str) first_time:    First time ("from").
        :param (str) second_time:   Second time ("to").
        :return (timedelta):        Difference between times.
        """

        # Convert times to datetime objects so that difference can be calculated
        from datetime import datetime
        datetime_format = "%Y-%m-%dT%H:%M:%S" # 24-hour clock
        first_time_in_datetime = datetime.strptime(first_time, datetime_format)
        second_time_in_datetime = datetime.strptime(second_time, datetime_format)

        # print("From {0} to {1}: ".format(first_time, second_time))
        difference = second_time_in_datetime - first_time_in_datetime # Timedelta object
        return(abs(difference))
    
    @staticmethod
    def timedelta_to_string(td): 
        """
        Converts a timedelta object to a string.

        :param (timedelta) td: Timedelta object (often representing a difference in time).
        :return (str):         Formatted string specifying days, hours, minutes, and seconds.
        """
        days    = divmod(td.total_seconds(), 86400)   # Get days (without [0]!)
        hours   = divmod(days[1], 3600)               # Use remainder of days to calc hours
        minutes = divmod(hours[1], 60)                # Use remainder of hours to calc minutes
        seconds = divmod(minutes[1], 1)               # Use remainder of minutes to calc seconds
        return "%d days, %d hours, %d minutes and %d seconds" % (days[0], hours[0], minutes[0], seconds[0])

    def process(self, user_data): 
        """
        For the DU and promotion stages specified by the user: 
        - Evaluates "X" amount of past versions of that DU which have successful promotion data at both stages.
        - Continues this process until has successfully analyzed the last "X" number of promotions as specified by the user (num_last_promotions_to_analyze)

        NOTE: Cannot simply query Seshat for 'promotedAt' times at diff stages as that might use diff versions of the same DU. 
              AKA, for a specific DU, the latest version ofpromoted to TESTREADY /= the latest version promoted to PROD.
        """        
        du_name = user_data['du_name']
        first_promotion_stage = user_data['first_promotion_stage']
        second_promotion_stage = user_data['second_promotion_stage']
        num_last_promotions_to_analyze = user_data['num_last_promotions_to_analyze (used to calculate an average time)']

        pointer = 0 # Used to iterate through the du_versions_list, esp. to skip a specific version does not have sufficient promo data
        counter = 0 # Used to track when target number of promotions to analyze has been hit
        dict_diffs = {}
        du_versions_list = Time.get_du_versions_list(du_name)
        print(du_versions_list)

        # Check if successfully received versions from Seshat
        if (len(du_versions_list) != 0): 

            while(counter != int(num_last_promotions_to_analyze)):

                # Specify the version to get promotion data for 
                du_version = du_versions_list[pointer]
                print("Evaluating version", du_version)

                # Check that promotion data for this version is available
                results = self.validate(du_name, du_version, first_promotion_stage, second_promotion_stage)
                got_promo_data = results[0]
                first_time = results[1]
                second_time = results[2]
                if(got_promo_data):
                    counter += 1 # Update

                    first_time = first_time[:-5]
                    second_time = second_time[:-5]

                    print("Version: ", du_version)
                    print("Time promoted to {}: ".format(first_promotion_stage), first_time)
                    print("Time promoted to {}: ".format(second_promotion_stage), second_time)

                    # Insert time between first stage and second stage for this specific version in dict_diffs
                    time_to_promote = Time.time_diff(first_time, second_time) # Timedelta object!
                    dict_diffs[du_version] = time_to_promote
                else: 
                    print("Could not find promotion data for", du_version + ". Moving on to next (earlier) promotion.")
                
                pointer += 1 # Always updates (moving through versions)

            # Calculate average time between versions to promotes from first_stage_input to second_stage_input
            if int(num_last_promotions_to_analyze) == 1: # Just calculate the diff in time
                avg = list(dict_diffs.values())[0]
            else:
                import datetime
                sum = datetime.timedelta(hours=0) 
                for key in dict_diffs:
                    promo_in_datetime = Time.timedelta_to_string(dict_diffs[key])
                    print("Version {0} took {1} to promote".format(key, promo_in_datetime))
                    sum += dict_diffs[key]
                avg = sum /len(dict_diffs)
            
            bot_response = "Average time to promote from {0} to {1}, based on the last {2} promotions: {3}".format(
                            first_promotion_stage, second_promotion_stage, num_last_promotions_to_analyze, Time.timedelta_to_string(avg))
        else: 
            bot_response = "Sorry, I could not find your DU. Please try again or refer to http://sww.sas.com/pdsweb/REDataPortal/."

        return bot_response