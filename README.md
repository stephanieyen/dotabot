# DOTA Bot

**Welcome to the DOTA Bot!**     
This was a proof-of-concept internship project with the DevOps Testing Automation (DOTA) team designed to answer common queries among different developer/tester teams. This README attempts to explain how it works so it can be adapted in the future.     
See my Jira epic with the original list of FAQs brainstormed by Mike Shelton and I: https://rndjira.sas.com/browse/DEVOPSTEST-64189   

**Inspo**: 
- This project follows a similar structure as the Chatterbot Python library (esp. the idea of logic adapters). See here: https://github.com/gunthercox/ChatterBot 
- This bot's UI was adapted from a boilerplate template: https://github.com/chamkank/flask-chatterbot 

**Creator**: Stephanie Yen (DOTA Intern, Summer 2021)    
*I will lose access to my SAS email, so please email me at my personal email (steph.yensy@gmail.com) if you have questions or are confused.*  

**Supporter**: Susanna Wallenberger  
*Knows best about getting this on an internal SAS server.*

---

## How It Works

### Summary

The main files to understand are:  
- *Python*: `app/routes.py`, `src/bot.py`, `src/logic/logic_adapter.py`
- *HTML/CSS/JavaScript*: `app/templates/index.html`
- *Queries database*: `app/models/py`, `src/storage/app.db`

The DOTA Bot is initialized in `app/routes.py` with all its associated logic adapters (more explanation on these below). 

**Bot flow**:
1. User enters a number corresponding to their query (based on ID in database).
2. Bot fetches and displays requirements for the user's query.
3. User puts in their data values correlating to the requirements.
4. Bot returns the final, customized anaswer.

The first two steps utilize the **/question** endpoint (GET request), and the last two steps utilize the **/answer** endpoint (POST request).  
Steps 2 and 4 use the `specify_requirements()` and `answer()` methods in `src/bot/py`, respectively. The first method ensures that the received input is a supported query ID. Both methods essentially loop through all of the bot's logic adapters and, when it finds the appropriate adapter to answer the user's question, return the associated requirements or processed answer.

See my Canva presentation for more details on the Python/JavaScript flow (slides 7-19): https://www.canva.com/design/DAEmGzE9H7M/c7HFi_Q-w_Sou6UWRYX5JA/view?utm_content=DAEmGzE9H7M&utm_campaign=designshare&utm_medium=link&utm_source=sharebutton  

### Directory Layout (dotabot)
- */app*
  - */static*: CSS 
  - */templates*: HTML 
  - *models.py*: creates the Queries database model for app.db using SQLAlchemy ORM, contains useful database functions that can be run via `flask shell`
  - *routes.py*: initializes the DOTA Bot and sets up routes for the Flask app
- */src*
  - */logic*: contains several logic adapters capable of answering the questions in `app.db`
  - */storage*
    - *app.db*: database of questions that the DOTA Bot is able to answer
    - *NA.yaml*: downloaded most recent version from https://gitlab.sas.com/dota/cruise/-/blob/main/src/deployment_tooling/orders/NA.yaml into folder (08/06/2021), consider how up-to-date it remains
  - *bot.py*: houses the Bot class (source of DOTA Bot logic)
- *config.py*: contains configuration settings for Flask app
- *main.py*: runs the Flask app
- *requirements.txt*

### Logic Adapters & Queries

A **logic adapter** can answer a single query or set of related queries which have the same requirements. Access specific logic adapter code for more details.  

Each **query** has three attributes:   
1. **ID**: Right now, the IDs are assigned in order of the questions below (1-10).
2. **Category**: Matches logic adapter class name.
3. **Query text**

Logic adapter | Supported queries | Requirements | Sources | Functionality notes (as of 08/06/2021)
-----      | -----                | -----        | -----   | -----
Collection | <ol><li>What new DUs were introduced at *promotionStage* on *date*?</li></ol>     | promotion_stage, date (YYYY-MM-DD)         | Seshat API            | Able to generate DUs from NA.yaml (which takes a long time), but as of 08/06/2021, querying Seshat by promotion stage is not returning any results. 
Confluence | <ol><li>What version of Kubernetes is DOTA running on *cadenceCluster*?</li></ol> | cadence_cluster                            | Confluence page (https://rndconfluence.sas.com/confluence/display/RNDDEVOPSTA/DOTA+Infrastructure+and+Commonly+Used+Resources)/API   | Works. User needs to type cadence cluster to exactly match the Confluence page source, so would suggest "related text" or displaying a list of supported options.
DUQueries  | <ol><li>What version of *DUName* is at *promotionStage*?</li><li>What lifecycle version of *DUName* is at *promotionStage*?</li><li>When was *DUName* promoted to *promotionStage*?</li></ol>                  | du_name, promotion_stage                  | Seshat API            | Works. Lifecycle version is often "Not Found" -- does not seem to be included in queried DU data (may have to look into this).
Orderables | <ol><li>Is *sellableUnitName* in the DOTA NA (nearly all) order?</li></ol>         | sellable_unit_name                        | NA.yaml               | Works.
Scribe     | <ol><li>What code changed (what were last *numCommits* changes) in the new build of *DUName*?</li></ol> | du_name, num_recent_commits | Scribe API, GitLab API | Works. Prints a list, so would improve formatting.
Support    | <ol><li>What are the currently supported DOTA deployments/cadences?</li></ol>      | none                                      | Octantis (Seshat API) | Usually works but sometimes does not because of `TypeError: string indices must be integers`, which is often fixed when you refresh the page. Not sure why...
Teemo      | <ol><li>Who are the test engineers for *DUName*?</li></ol>                         | du_name (must start with quest_tools_)    | Teemo API         | Works. (e.g., quest_tools_cmp, quest_tools_speech, quest_tools_textsummarizationtests)
Time       | <ol><li>How long did it take *DUName* to promote from *promotionStage1* to *promotionStage2*? (e.g., TESTREADY to PROD)"</li></ol> | du_name, first_promotion_stage, second_promotion_stage, num_last_promotions_to_analyze    | Seshat API    | Also usually works, but sometimes unpredictable/requires refreshing the page. Some requests in get_du_versions_list were returning empty lists for varying DU's, but this seemed to be fixed by 08/06/2021. Some requests (e.g., "sas-cas-server") also take much longer to load since all the versions data is being fetched.

---

## FAQ

### How do I run the Flask app on my computer?
1. `python -m venv venv`
2. `source venv/bin/activate`
3. `export FLASK_APP=main.py` (make sure you are in the main `dotabot` folder)
4. `flask run`

### How do I add a new query?
1. Identify the requirements and sources of your query. Once you have tested a successful API request/etc. to get what you need, you are pretty set to go.
2. Create a new logic adapter child class with category and requirements specified in the constructor. Write your main logic in a `process()` method and add supporting static methods as necessary.
3. Make sure to account for any request failures and return error messages if so. Also make sure to account for case-insensitivity for user inputs.
4. Add your logic adapter in the DOTA Bot initialization in `routes.py`.
5. Add your query (with a unique ID) to `app.db` (the database is called Queries). I personally did this using `flask shell` while in venv mode on my computer. Below are all the commands I ran to add the queries in one go. Reference here: https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-iv-database 

```
db.session.add(Queries(id=1, category="collection", query_text="What new DUs were introduced at <promotionStage> on <date>?"))
db.session.add(Queries(id=2, category="confluence", query_text="What version of Kubernetes is DOTA running on <cadenceCluster>?"))
db.session.add(Queries(id=3, category="du_queries", query_text="What version of <DUName> is at <promotionStage>?"))
db.session.add(Queries(id=4, category="du_queries", query_text="What lifecycle version of <DUName> is at <promotionStage>?"))
db.session.add(Queries(id=5, category="du_queries", query_text="When was <DUName> promoted to <promotionStage>?"))
db.session.add(Queries(id=6, category="orderables", query_text="Is <sellableUnitName> in the DOTA NA (nearly all) order?"))
db.session.add(Queries(id=7, category="scribe", query_text="What code changed (what were last <numCommits> changes) in the new build of <DUName>?"))
db.session.add(Queries(id=8, category="support", query_text="What are the currently supported DOTA deployments/cadences?"))
db.session.add(Queries(id=9, category="teemo", query_text="Who are the test engineers for <DUName>?"))
db.session.add(Queries(id=10, category="time", query_text="How long did it take <DUName> to promote from <promotionStage1> to <promotionStage2>? (e.g., TESTREADY to PROD)"))
db.session.commit() // Make sure to do this so save db changes.
queries = Queries.query.all() // Useful to view what is currently in the Queries database.
```

## Features to consider adding

**General design**
- Right now, there are a few print statements in the project (print in the CLI) -- consider logging messages somewhere else.
- Allow the user to quit out of a question. Right now, as soon as the user puts in a supported query ID, they have to complete the 2-step process.
- Exit a process if an answer takes too long to load. (Bot shows "Loading...")
- Allow users to type in a question and automatically save it to the Queries database and/or some kind of ticketing system (e.g., ServiceNow) if it is not pre-configured. 
- Display queries in a separate place (e.g., popup).
- Save user data in one "session" (so they don't have to retype requirements, such as "du_name").

**Deployment**
- Deploy as a VSCode extension interface: https://code.visualstudio.com/api/working-with-extensions/publishing-extension#packaging-extensions

**Overall chatbot revamps**
- Look into no-code/low-code chatbot tools (SAS Conversation Designer is an option, and a Viya4 product!).
- Allow for more flexibility (for example, the user currently has to respond to the requirements in a very specific way).
- Similarly, look into related text if considering the possibility of the user manually typing out their query (Python libraries like spaCy).
- If possible, potential "auto-complete" features (like Google does).
- Account for confidence and returning multiple results like the Chatterbot library does.
- Make separate chatbots for separate types of queries/functions with modular or reusable code.