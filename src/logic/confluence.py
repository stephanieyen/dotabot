import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

import requests
import re 

class Confluence(LogicAdapter):
    """
    SUPPORTED QUERIES
        1. What version of Kubernetes is DOTA running on <cadence_cluster>?
    
    REQUIREMENTS
        * cadence_cluster

    SOURCES
        * Confluence page/API: https://rndconfluence.sas.com/confluence/display/RNDDEVOPSTA/DOTA+Infrastructure+and+Commonly+Used+Resources
    """

    def __init__(self, chatbot, category="confluence", requirements="cadence_cluster"):
        super().__init__(chatbot, category, requirements)


    def process(self, user_data): 
        cadence_cluster = user_data["cadence_cluster"].lower() # Case-insensitive

        # Set up Confluence API
        confluenceBaseUrl = 'https://rndconfluence.sas.com/confluence/'
        contentApiUrl = '/rest/api/content'
        pageId = '63674717'
        confluence_url = '{confluenceBaseUrl}{contentApiUrl}/{pageId}?expand=body.storage'.format(confluenceBaseUrl=confluenceBaseUrl, contentApiUrl=contentApiUrl, pageId=pageId)

        # Confluence API request
        resp = requests.get(confluence_url)

        # Use RegEx to find portions matching cadence clusters to K8s versions
        text = resp.text
        pattern = "\>([^>]* - K8S [0-9].[0-9][0-9].[0-9][^<]*)\<"
        """
        Example:    Release TestReady (TR) Cluster - K8S 1.19.8
                    In resp.text, this is between '>' and '<'

        \>                      # Escaped parenthesis, "starts with a '>' character"
        (                       # Capture the stuff in between
        [^>]                    # Any character that is not '>'
        *                       # Zero or more occurrences of the aforementioned "non '>' char"
        - K8S                   # Text
        [0-9].[0-9][0-9].[0-9]  # K8s version formatting
        [^<]                    # Any character that is not '<'
        *                       # Zero or more occurrences of the aforementioned "non '<' char"
        )                       # Close the capturing group
        \<                      # Ends with a '<' character

        """
        matches = re.findall(pattern, text) # List of all found matches
        # print(matches)

        # Create dict mapping cadence clusters (keys) to K8s versions (values)
        matches_dict = {}
        for match in matches: 
            cadence = match.split(' - ')[0].lower()
            kubernetes_version = match.split(' - ')[1]
            matches_dict[cadence] = kubernetes_version

        # Find K8s version based on input (cadence cluster key)
        try: 
            bot_response = matches_dict[cadence_cluster]
            return bot_response
        except KeyError: 
            bot_response = "Sorry, I could not find your cluster. Please try again or refer to https://rndconfluence.sas.com/confluence/display/RNDDEVOPSTA/DOTA+Infrastructure+and+Commonly+Used+Resources."
            return bot_response

