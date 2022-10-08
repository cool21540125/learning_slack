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

@slack_event_adapter.on("message")
def message(payload):
    event = payload.get("event", {})
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text")
    # print('=====')
    # print(payload)
    # print('=====')
    if BOT_ID != user_id:
        if user_id in message_counts:
            message_counts[user_id] += 1
        else:
            message_counts[user_id] = 1
        
        client.chat_postMessage(channel=channel_id, text=text)


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
