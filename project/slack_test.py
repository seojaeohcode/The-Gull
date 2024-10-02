import json
from flask import Flask, request, make_response

app = Flask(__name__)

@app.route('/', methods=['POST'])
def hello_there():
    slack_event = json.loads(request.data)
    
    # Slack에서 온 'challenge' 요청을 처리하고 응답
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"Content-Type": "application/json"})
    
    return make_response("There are no slack request events", 404, {"X-Slack-No-Retry": 1})

if __name__ == '__main__':
    app.run()
