from flask import Flask, Response, request
import slack
import os
from dotenv import load_dotenv
from slackeventsapi import SlackEventAdapter
from pathlib import Path

env_path = Path(".") / ".env"
load_dotenv(dotenv_path=env_path)

app = Flask(__name__)
slack_event_adapter = SlackEventAdapter(
    os.environ["SIGNING_SECRET"], "/slack/events", app)

client = slack.WebClient(token=os.environ["SLACK_TOKEN"])
BOT_ID = client.api_call("auth.test")["user_id"]

message_counts = {}
welcome_message = {}

class WelcomeMessage:
    START_TEXT = {
        'type': 'section',
        'text': {
            'type': 'mrkdwn',
            'text': (
                '這個是 Slack Markdown 的 Reply, 支援情況如下:\n\n'
                '# ❌<h1>\n\n'
                '*✔️ 一顆星 ~斜體~ 粗體*\n\n'
                '**❌ ~粗體~**\n\n'
                '`✔️ 程式碼區塊`'
            )
        }
    }

    DIVIDER = {'type': 'divider'}

    def __init__(self, channel, user):
        self.channel = channel
        self.icon_emoji = ':robot_face:'
        self.timestamp = ''
        self.completed = False

    def get_message(self):
        return {
            'ts': self.timestamp,
            'channel': self.channel,
            'username': '你誰啊',
            'icon_emoji': self.icon_emoji,
            'blocks': [
                self.START_TEXT,
                self.DIVIDER,
                self._get_reaction_task()
            ]
        }

    def _get_reaction_task(self):
        checkmark = ':white_check_mark:'
        if not self.completed:
            checkmark = ':white_large_square:'

        text = f'{checkmark} *Is Reply*'

        return {'type': 'section', 'text': {'type': 'mrkdwn', 'text': text}}


def send_welcome_message(channel, user):
    welcome = WelcomeMessage(channel, user)
    message = welcome.get_message()
    # print("===")
    # print(message)
    # print("===")
    response = client.chat_postMessage(**message)
    welcome._timestamp = response["ts"]

    if channel not in welcome_message:
        welcome_message[channel] = {}
    welcome_message[channel][user] = welcome


@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    # print('=====')
    # print(payload)
    # print(user_id)
    # print('=====')
    if user_id != None and BOT_ID != user_id:
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1
        
        if text.lower() == "start":
            send_welcome_message(channel_id, user_id)


@app.route("/demo-message-count", methods=["POST"])
def demo_message_count():
    data = request.form
    user_id = data.get('user_id')
    channel_id = data.get('channel_id')
    message_count = message_counts.get(user_id, 0)

    client.chat_postMessage(
        channel=channel_id, text=f"/demo-message-count 成功!\nMessage: {message_count}")
    return Response(), 200


if __name__ == "__main__":
    app.run(debug=True, port=3001)
