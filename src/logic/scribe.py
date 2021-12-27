import os, sys
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from src.logic.logic_adapter import LogicAdapter

import requests 
from pprint import pprint

class Scribe(LogicAdapter):
    """
    SUPPORTED QUERIES
        1. What code changed (what were the last <numCommits> changes) in the new build of <DUName>?
    
    REQUIREMENTS
        * du_name
        * num_recent_commits

    SOURCES
        * Scribe API
        * GitLab API
    """

    scribe_url = "https://scribe.unx.sas.com/d-scribe/api/v1/deployableUnits"

    def __init__(self, chatbot, category="scribe", requirements="du_name, num_recent_commits"):
        super().__init__(chatbot, category, requirements)

    @staticmethod
    def _parse_repo_url(pre_url): 
        """
        Parses a GitLab URL so it is suitable for the API.
        EX: https://gitlab.sas.com/dockerpkg/dkrcasall to https://gitlab.sas.com/api/v4/projects/dockerpkg%2Fdkrcasall/repository/commits
        """
        namespace = pre_url.split('/')[3]
        project_path = pre_url.split('/')[4]
        post_url = "https://gitlab.sas.com/api/v4/projects/" + namespace + "%2F" + project_path + "/repository/commits?with_stats=True"
        return post_url

    def process(self, user_data): 
        """
        NOTE: Uses the first GitLab link returned by the Scribe API. 
        More than 1 URL might be associated with the same DU name (e.g., "sas-conversation-designer-app"); in this case, they are also shared in the response.
        """
        du_name = user_data["du_name"]
        num_recent_commits = int(user_data["num_recent_commits"])

        # Set up Scribe API
        params = { "name": du_name }

        # Scribe API request
        resp = requests.get(self.scribe_url, params=params)
        if resp.status_code == 200: 
            gitlab_urls = []
            if isinstance(resp.json(), list):
                for project in resp.json(): 
                    gitlab_urls.append(project.get('replicationURL', "Not Found"))
            
        # Set up GitLab API (if there is a link)
        if (len(gitlab_urls) != 0):
            gitlab_url = gitlab_urls[0]
            gitlab_url_parsed = Scribe._parse_repo_url(gitlab_url)             
            headers = { 'Authorization': 'Bearer Uh1TaQ3MkWLGkjVYQBLz' }    # Personal/project access token to authenticate the GitLab API

            num = 0
            resp = requests.get(gitlab_url_parsed, headers=headers)
            if resp.status_code == 200: 
                commit_dict = {}
                if isinstance(resp.json(), list): # List of dicts (each commit is a dict)
                    for commit in resp.json()[:num_recent_commits]: 
                        num += 1
                        commit_details = []
                        commit_details.append("Committer name: " + commit['committer_name']) 
                        commit_details.append("Committed date: " + commit['committed_date']) 
                        commit_details.append("ID: " + commit['id'])
                        commit_details.append("Title: " + commit['title'])
                        commit_details.append("Stats: " + str(commit['stats']))
                        # commit['message'] often repeats title, so omit
                        # commit['web_url'] has ID, so omit

                        commit_dict["Commit #{}".format(num)] = commit_details

                bot_response_parts = []
                bot_response_parts.append("Evaluating " + gitlab_url)
                bot_response_parts.append(str(commit_dict))
                # Display other GitLab URLs
                if(len(gitlab_urls) > 1):
                    bot_response_parts.append("Other links found.")
                    bot_response_parts.append(str(gitlab_urls[1:]))
                bot_response = '\n'.join(bot_response_parts) 
        else: 
            bot_response = "Sorry, I could not find your DU. Please try again or refer to https://scribe.unx.sas.com/d-scribe/."

        return bot_response