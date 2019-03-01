import os
import time
import re
import sys
from slackclient import SlackClient

#html parsing
import urllib.request
from bs4 import BeautifulSoup

# instantiate Slack client
slack_client = SlackClient(os.environ.get("SLACK_BOT_TOKEN"))
# starterbot's user ID in Slack: value is assigned after the bot starts up
starterbot_id = None

# constants
RTM_READ_DELAY = 1 # 1 second delay between reading from RTM
EXAMPLE_COMMAND = "do"
MENTION_REGEX = "^<@(|[WU].+?)>(.*)"

def parse_bot_commands(slack_events):
    """
        Parses a list of events coming from the Slack RTM API to find bot commands.
        If a bot command is found, this function returns a tuple of command and channel.
        If its not found, then this function returns None, None.
    """
    for event in slack_events:
        if event["type"] == "message" and not "subtype" in event:
            user_id, message = parse_direct_mention(event["text"])
            if user_id == starterbot_id:
                return message, event["channel"]
    return None, None

def parse_direct_mention(message_text):
    """
        Finds a direct mention (a mention that is at the beginning) in message text
        and returns the user ID which was mentioned. If there is no direct mention, returns None
    """
    matches = re.search(MENTION_REGEX, message_text)
    # the first group contains the username, the second group contains the remaining message
    return (matches.group(1), matches.group(2).strip()) if matches else (None, None)

def handle_command(command, channel):
    """
        Executes bot command if the command is known
    """
    #print("X%sX"%command)

    # Default response is help text for the user
    default_response = """Not sure what you mean. Try "lunch" or *{}*.""".format(EXAMPLE_COMMAND)

    # Finds and executes the given command, filling in response
    response = None
    # This is where you start to implement more commands!
    if command.startswith(EXAMPLE_COMMAND):
        response = "Sure...write some more code then I can do that!"
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=response or default_response,
            user=starterbot_id,
            as_user="true")
    elif command == "lunch":
        #print("lunch command")
        blocks = parseFooda("broad")
        #print(blocks)
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            user=starterbot_id,
            as_user="true",
            blocks=blocks
            )
    else:
        slack_client.api_call(
            "chat.postMessage",
            channel=channel,
            text=default_response,
            user=starterbot_id,
            as_user="true")
            
#    print(starterbot_id)

#    print(response)

    # Sends the response back to the channel
 
def parseFooda(where):
    """
        Gets and parses menu for Broad or MGH
    """
    uri = ""
    if where == "broad":
        uri = "http://fooda.com/broadinstitute"
    elif where == "simches":
        uri = "http://fooda.com/simches"
    html = urllib.request.urlopen(uri)
    parsed_html = BeautifulSoup(html, features="html.parser")

#    print(parsed_html)

    restaurant = parsed_html.find_all("div", class_="restaurant-banner__name")
    location = parsed_html.find_all("div", class_="restaurant-banner__location")
    location_rough = parsed_html.find_all("div", class_="restaurant-banner__customer")
    img = parsed_html.find_all("img", class_="restaurant-banner__logo")
    description = parsed_html.find_all("div", class_="restaurant-banner__description")
    time = parsed_html.find_all("div", class_="restaurant-banner__time")

    link = parsed_html.find_all("a", class_="secondary-bar__tab myfooda-link")

    clickableLink = "https://app.fooda.com%s"%link[0]["href"]
    text = "*<%s|%s>*\\n%s - %s\\n%s\\n%s" % (clickableLink, restaurant[0].contents[0], location[0].contents[0], location_rough[0].contents[0], time[0].contents[0], description[0].contents[0])
#    print(restaurant[0].contents[0])
#    print(time[0].contents[0])
#    print(location[0].contents[0])
#    print(description[0].contents[0])
    imgSrc = img[0]['src']
    altText = "%s logo"%(restaurant[0].contents[0])

    block = """[
        {
        "type": "image",
        "image_url": "%s",
        "alt_text": "%s"
        },
        {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": "%s"
        }
    }
    ]"""%(imgSrc, altText, text)
    return (block)

if __name__ == "__main__":
#    parseFooda("simches")
    if len(sys.argv) > 1:
        if sys.argv[1] == "post":
            handle_command("lunch", "the-lab-lunch-project")
    else:
        if slack_client.rtm_connect(with_team_state=False):
            #print("Fooda Bot connected and running!")
            # Read bot's user ID by calling Web API method `auth.test`
            starterbot_id = slack_client.api_call("auth.test")["user_id"]
            while True:
                command, channel = parse_bot_commands(slack_client.rtm_read())
                if command:
                    handle_command(command, channel)
                time.sleep(RTM_READ_DELAY)
        else:
            print("Connection failed. Exception traceback printed above.")
