import json
import os
from flask import Flask, request, make_response
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

app = Flask(__name__)

# Docker에서 설정된 환경 변수에서 SLACK_BOT_TOKEN을 불러옴
token = os.getenv("SLACK_BOT_TOKEN")
print(f"SLACK_BOT_TOKEN: {token}")  # 확인용 출력

# Slack WebClient 설정
if token:
    client = WebClient(token)
    print("Slack client initialized")
else:
    print("SLACK_BOT_TOKEN is not set!")

@app.route('/', methods=['POST'])
def hello_there():
    slack_event = json.loads(request.data)
    
    # Slack에서 온 'challenge' 요청을 처리하고 응답
    if "challenge" in slack_event:
        return make_response(slack_event["challenge"], 200, {"Content-Type": "application/json"})
    
    return make_response("There are no slack request events", 404, {"X-Slack-No-Retry": 1})

# '/hello' Slash Command 처리 라우트
@app.route('/hello', methods=['POST'])
def slash_hello():
    slack_event = request.form  # Slash command는 form data로 전달됨
    print(f"Received event: {slack_event}")  # 이벤트 데이터를 출력하여 확인
    
    channel_id = slack_event.get('channel_id')  # 명령어가 발생한 채널 ID
    print(f"Channel ID: {channel_id}")  # 채널 ID 출력

    # Slash Command '/hello' 처리
    if slack_event.get('command') == '/인사':  # 명령어가 '/hello'일 때
        try:
            # chat.postMessage API를 통해 채널에 메시지 보내기 (봇이 보냄)
            response = client.chat_postMessage(
                channel=channel_id,  # 메시지를 보낼 채널 ID
                text="Hello, everyone!",  # 메시지 내용
                username="데굴이",  # 봇의 사용자명을 "데굴이"로 변경
                icon_emoji=":bird:"  # 봇의 아이콘 설정 (이모지)
            )
            return make_response("Message sent to the channel", 200)
        
        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")  # 에러 메시지 출력
            error_message = f"Error sending message: {e.response['error']}"
            return make_response(error_message, 500)
    
    return make_response("Command not recognized", 404)

# '/chatlog' Slash Command 처리 라우트
@app.route('/chatlog', methods=['POST'])
def slash_chatlog():
    slack_event = request.form  # Slash command는 form data로 전달됨
    channel_id = slack_event.get('channel_id')  # 명령어가 발생한 채널 ID 가져오기
    print(f"Channel ID: {channel_id}")  # 채널 ID 출력

    # Slash Command '/chatlog' 처리
    if slack_event.get('command') == '/채팅내역':  # 명령어가 '/chatlog'일 때
        try:
            # conversations.history API를 통해 채널 메시지 기록 가져오기
            result = client.conversations_history(channel=channel_id)
            
            # 각 메시지의 텍스트를 가져와 포맷팅
            messages = result["messages"]
            message_texts = [f"{message['user']}: {message['text']}" for message in messages]
            chat_log = "\n".join(message_texts[:10])  # 최근 10개의 메시지만 표시
            
            # 채팅 기록을 채널에 메시지로 보내기 (봇이 보냄)
            response = client.chat_postMessage(
                channel=channel_id,  # 메시지를 보낼 채널 ID
                text=f"Here is the chat history:\n{chat_log}",  # 채팅 기록
                username="데굴이",  # 봇의 사용자명을 "데굴이"로 변경
                icon_emoji=":bird:"  # 봇의 아이콘 설정 (이모지)
            )
            
            return make_response("Chat log sent to the channel", 200)
        
        except SlackApiError as e:
            print(f"Slack API error: {e.response['error']}")  # 에러 메시지 출력
            error_message = f"Error fetching or sending chat history: {e.response['error']}"
            return make_response(error_message, 500)
    
    return make_response("Command not recognized", 404)


if __name__ == '__main__':
    app.run(debug=True)