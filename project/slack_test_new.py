import threading
import json
import os
import torch
from flask import Flask, request, make_response, send_file
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from datetime import datetime
import numpy as np

# Matplotlib 백엔드 설정 (가장 상단에 위치)
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

import io
import re
import seaborn as sns

# IBM Watsonx AI 관련 모듈 임포트
from dotenv import load_dotenv
from ibm_watsonx_ai import APIClient
from ibm_watsonx_ai.foundation_models import Embeddings
from ibm_watsonx_ai.metanames import EmbedTextParamsMetaNames as EmbedParams
from langchain_ibm import WatsonxLLM
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans

# Flask 애플리케이션 초기화
app = Flask(__name__)

# 환경 변수 로드
load_dotenv()

# Slack API 토큰
bot_token = os.getenv("SLACK_BOT_TOKEN")

# IBM API 키 및 프로젝트 ID
IBM_API_KEY = os.getenv("IBM_API_KEY")
PROJECT_ID = os.getenv("PROJECT_ID")

# 필수 환경 변수 체크
if not bot_token:
    raise EnvironmentError("SLACK_BOT_TOKEN is not set!")

if not IBM_API_KEY or not PROJECT_ID:
    raise EnvironmentError("IBM_API_KEY or PROJECT_ID is not set!")

# Slack WebClient 설정
client = WebClient(token=bot_token)
print("Slack client initialized")

# 로컬 이미지 파일 경로
# LOCAL_IMAGE_PATH = 'C:/Users/HB/Downloads/desktopAPP/desktopAPP/thegull_profile_photoes/thegull_smile.png'

# 이미지 제공 엔드포인트
# @app.route('/deguli_profile_image')
# def deguli_profile_image():
#     return send_file(LOCAL_IMAGE_PATH, mimetype='image/png')

# IBM Watsonx AI 클라이언트 설정
wx_credentials = {
    "url": "https://us-south.ml.cloud.ibm.com",
    "apikey": IBM_API_KEY
}

# APIClient 초기화
wx_client = APIClient(wx_credentials)

if wx_client:
    print("IBM Watsonx AI Client initialized successfully.")
else:
    print("Failed to initialize IBM Watsonx AI Client.")

# 임베딩 모델 설정
EMBEDDING_MODEL_ID = wx_client.foundation_models.EmbeddingModels.MULTILINGUAL_E5_LARGE

embed_params = {
    EmbedParams.TRUNCATE_INPUT_TOKENS: 128,
    EmbedParams.RETURN_OPTIONS: {
        'input_text': True
    }
}

# 임베딩 모델 초기화
embedding_model = Embeddings(
    model_id=EMBEDDING_MODEL_ID,
    credentials=wx_credentials,
    params=embed_params,
    project_id=PROJECT_ID,
    space_id=None,
    verify=False
)

# LLM 모델 설정
os.environ["WATSONX_APIKEY"] = IBM_API_KEY

MODEL_ID_list = {
    'mistral-large': 'mistralai/mistral-large',
    'mixtral-8x7b': 'mistralai/mixtral-8x7b-instruct-v01',
    'llama3-70b': 'meta-llama/llama-3-1-70b-instruct',
    'llama3-8b': 'meta-llama/llama-3-1-8b-instruct',
}

parameters = {
    "decoding_method": "greedy",
    "max_new_tokens": 500,
    "repetition_penalty": 1.1,
    # "stop_sequences": ["\n"],  # 문제가 발생하면 제거
}

MODEL_NAME = 'llama3-70b'

watsonx_llm = WatsonxLLM(
    model_id=MODEL_ID_list[MODEL_NAME],
    url="https://us-south.ml.cloud.ibm.com",
    project_id=PROJECT_ID,
    params=parameters,
)

# 한글 폰트 설정 함수
def set_korean_font():
    import platform
    system_name = platform.system()
    if system_name == 'Windows':
        font_name = 'Malgun Gothic'
    elif system_name == 'Darwin':  # macOS
        font_name = 'AppleGothic'
    else:
        font_name = 'NanumGothic'  # 리눅스 등

    plt.rc('font', family=font_name)
    plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 기본 경로 설정. 슬랙 요청의 'challenge' 필드가 있을 경우 해당 내용을 응답해 Slack 요청을 확인
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
    try:
        slack_event = request.form
        print(f"Received event: {slack_event}")  # 이벤트 데이터를 출력하여 확인

        # Slack에서 명령어가 발생한 채널 ID 추출
        channel_id = slack_event.get('channel_id')
        if not channel_id:
            print("Channel ID not found in the request.")
            return make_response("Channel ID not found", 400)
        print(f"Channel ID: {channel_id}")  # 채널 ID 출력

        # '/인사' 명령어를 인식하고 Slack 메시지를 전송
        command = slack_event.get('command')
        print(f"Command: {command}")

        if command == '/인사':
            try:
                # 블록 구성
                blocks = [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*안녕하세요! 데굴르~ 데굴이에요!* 🐦\n저는 팀플과 조별과제가 데굴데굴 잘 굴러가게 도와주는 똑똑한 도우미랍니다! 다양한 분석과 재미있는 기능들로 여러분의 협업을 더욱 원활하게 만들어드려요. 궁금한 점이 있다면 언제든지 저를 불러주세요!"
                        }
                    },
                    {
                        "type": "divider"
                    },
                    {
                        "type": "context",
                        "elements": [
                            {
                                "type": "mrkdwn",
                                "text": "저는 `/발화량`, `/메시지수`, `/반응수`, `/주제유사도` 같은 커맨드로 다양한 분석을 해드릴 수 있어요!"
                            }
                        ]
                    }
                ]

                # 프로필 이미지 URL 설정 (제거됨)

                response = client.chat_postMessage(
                    channel=channel_id,
                    blocks=blocks,
                    text="안녕하세요! 데굴이에요!"  # 메시지 미리보기에서 보이는 텍스트
                    # username="데굴이",  # 제거
                    # icon_url=image_url,  # 제거
                    # as_user=False  # 제거
                )
                print(f"Message sent: {response}")
                return make_response("", 200)
            except SlackApiError as e:
                print(f"Slack API error: {e.response['error']}")
                error_message = f"Error sending message: {e.response['error']}"
                return make_response(error_message, 500)
            except Exception as e:
                print(f"Unexpected error in slash_hello: {e}")
                return make_response("Internal Server Error", 500)
        else:
            print("Command not recognized")
            return make_response("Command not recognized", 404)
    except Exception as e:
        print(f"Error processing the request: {e}")
        return make_response("Internal Server Error", 500)

# Slack 타임스탬프를 읽기 쉬운 시간 형식으로 변환
def convert_timestamp_to_readable(ts):
    return datetime.utcfromtimestamp(float(ts)).strftime('%Y-%m-%d %H:%M:%S')

# 채널에서 채팅 로그를 가져오는 함수
def get_chatlog(channel_id, target='user'):
    try:
        chat_logs = []
        has_more = True
        next_cursor = None
        user_cache = {}  # 사용자 정보 캐싱

        auth_response = client.auth_test()
        bot_user_id = auth_response['user_id']

        # 채널의 모든 메시지를 수집
        while has_more:
            result = client.conversations_history(
                channel=channel_id,
                cursor=next_cursor,
                limit=200  # 최대 200개의 메시지를 한 번에 가져올 수 있음
            )

            messages = result["messages"]

            for message in messages:
                user_id = message.get('user')
                if not user_id:
                    continue  # 시스템 메시지 등 사용자 정보가 없는 경우 건너뜀

                # 사용자 정보 캐싱
                if user_id in user_cache:
                    username = user_cache[user_id]
                else:
                    user_info = client.users_info(user=user_id)
                    if not user_info['ok']:
                        continue
                    # display_name을 먼저 시도하고, 없으면 real_name, 없으면 name을 사용
                    username = user_info['user']['profile'].get('display_name') or user_info['user']['real_name'] or user_info['user']['name']
                    print(username)
                    user_cache[user_id] = username

                # 특정 사용자만 포함할지 선택
                if target == 'user' and user_id == bot_user_id:
                    continue
                elif target == 'bot' and user_id != bot_user_id:
                    continue

                chat_logs.append({
                    "user_id": user_id,
                    "username": username,
                    "text": message.get('text'),
                    "timestamp": message.get('ts'),
                    "reactions": message.get('reactions', [])
                })

            has_more = result.get('has_more', False)
            next_cursor = result.get('response_metadata', {}).get('next_cursor')

        # 시간순 정렬 (오래된 메시지부터)
        chat_logs.reverse()

        return chat_logs

    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        return None
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None

# 사용자 참여도 분석 함수
def analyze_participation(chat_logs, analysis_type):
    participation_scores = {}
    total_value = 0  # 전체 합계

    for log in chat_logs:
        user_id = log['user_id']
        username = log['username']

        if user_id not in participation_scores:
            participation_scores[user_id] = {'username': username, 'text_length': 0, 'message_count': 0, 'reaction_count': 0}

        if analysis_type == 'speech_amount':
            text_length = len(log['text'])
            participation_scores[user_id]['text_length'] += text_length
            total_value += text_length

        elif analysis_type == 'message_count':
            participation_scores[user_id]['message_count'] += 1
            total_value += 1

        elif analysis_type == 'reaction_count':
            reactions = log.get('reactions', [])
            reaction_total = sum(reaction.get('count', 0) for reaction in reactions)
            participation_scores[user_id]['reaction_count'] += reaction_total
            total_value += reaction_total

    # 각 멤버별로 전체 대비 비율 및 값을 저장
    for user_id, scores in participation_scores.items():
        if analysis_type == 'speech_amount':
            value = scores['text_length']
            scores['percentage'] = (value / total_value) * 100 if total_value > 0 else 0
            scores['value'] = value
        elif analysis_type == 'message_count':
            value = scores['message_count']
            scores['percentage'] = (value / total_value) * 100 if total_value > 0 else 0
            scores['value'] = value
        elif analysis_type == 'reaction_count':
            value = scores['reaction_count']
            scores['percentage'] = (value / total_value) * 100 if total_value > 0 else 0
            scores['value'] = value

    return participation_scores

# 참여도 차트 생성 함수
def create_participation_chart(participation_scores, analysis_type):
    set_korean_font()  # 한글 폰트 설정

    # 참여도 높은 순으로 정렬
    sorted_participation = sorted(participation_scores.items(), key=lambda x: x[1]['value'], reverse=True)

    usernames = [scores['username'] for user_id, scores in sorted_participation]
    values = [scores['value'] for user_id, scores in sorted_participation]

    if analysis_type == 'speech_amount':
        title = '발화량 비율'
    elif analysis_type == 'message_count':
        title = '메시지 수 비율'
    elif analysis_type == 'reaction_count':
        title = '반응 수 비율'
    else:
        title = '참여도 분석 결과'

    total = sum(values)
    autopct = lambda p: '{:.1f}%\n({:.0f})'.format(p, (p * total / 100))

    # 색상 리스트 정의 (필요에 따라 추가)
    colors = ['gold', 'lightskyblue', 'lightcoral']

    # 가장 첫 번째 요소(가장 큰 값)에만 0.1을 할당하고, 나머지는 0으로 설정
    explode = [0.1] + [0] * (len(values) - 1)

    plt.figure(figsize=(8, 6))
    patches, texts, autotexts = plt.pie(
        values, 
        labels=usernames, 
        autopct=autopct, 
        startangle=90, 
        counterclock=False, 
        colors=colors, 
        shadow=True,
        explode=explode
    )

    # 범례 추가
    plt.legend(patches, usernames, loc="best")

    # 축 균등 설정 (원형 유지)
    plt.axis('equal')

    # 제목 설정: 좌측 상단 위치, 폰트 크기 증가
    plt.title(title, loc='left', fontsize=20)

    # 레이아웃 조정
    plt.tight_layout()

    # 이미지 버퍼로 저장
    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close()

    return img_buf

# 참여도 분석 결과를 위한 블록 생성 함수
def format_participation_blocks(participation_scores, analysis_type):
    # 참여도 높은 순으로 정렬
    sorted_participation = sorted(participation_scores.items(), key=lambda x: x[1]['value'], reverse=True)
    top_user_username = sorted_participation[0][1]['username']

    # 총합계 계산
    total_value = sum(scores['value'] for user_id, scores in sorted_participation)
    average_value = total_value / len(sorted_participation) if sorted_participation else 0
    values = [scores['value'] for user_id, scores in sorted_participation]
    max_value = max(values) if values else 0
    min_value = min(values) if values else 0

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*참여도 분석 결과입니다!* :sparkles:"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*총합계:* {total_value}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*평균:* {average_value:.2f}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*최대값:* {max_value}"
                },
                {
                    "type": "mrkdwn",
                    "text": f"*최소값:* {min_value}"
                }
            ]
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":crown: 참여도 MVP는 *{top_user_username}* 님 입니다! 정말 대단해요!"
            }
        },
        {"type": "divider"}
    ]

    # 각 멤버별 결과 추가
    for user_id, scores in sorted_participation:
        percentage = scores.get('percentage', 0)
        value = scores['value']
        if analysis_type == 'speech_amount':
            text = f"*{scores['username']}* 님: {value} 글자 ({percentage:.1f}%)"
        elif analysis_type == 'message_count':
            text = f"*{scores['username']}* 님: {value} 메시지 ({percentage:.1f}%)"
        elif analysis_type == 'reaction_count':
            text = f"*{scores['username']}* 님: {value} 반응 ({percentage:.1f}%)"

        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                }
            }
        )

    return blocks

# 참여도 분석 실행 함수
def handle_participation_analysis(channel_id, analysis_type):
    try:
        chat_logs = get_chatlog(channel_id)
        if not chat_logs:
            client.chat_postMessage(
                channel=channel_id,
                text="앗! 채팅 로그를 가져오는 중 문제가 발생했어요."
            )
            return

        participation_scores = analyze_participation(chat_logs, analysis_type)
        img_buf = create_participation_chart(participation_scores, analysis_type)
        analysis_titles = {
            'speech_amount': '발화량 분석 결과',
            'message_count': '메시지 수 분석 결과',
            'reaction_count': '반응 수 분석 결과'
        }

        # 결과 이미지 업로드
        upload_response = client.files_upload_v2(
            channel=channel_id,
            file=img_buf,
            filename='participation_analysis.png',
            title=analysis_titles.get(analysis_type, '참여도 분석 결과')
        )

        blocks = format_participation_blocks(participation_scores, analysis_type)

        client.chat_postMessage(
                channel=channel_id,
                blocks=blocks,
                text="참여도 분석 결과입니다!"
        )
        
        # if upload_response['ok']:
        #     # 업로드된 파일의 정보
        #     file_info = upload_response['file']
        #     file_url = file_info.get('permalink_public')  # 공개 URL 확보

        #     if not file_url:
        #         # permalink_public이 없는 경우
        #         client.chat_postMessage(
        #             channel=channel_id,
        #             text="앗! 이미지를 공개적으로 공유하는 데 문제가 발생했어요."
        #         )
        #         return

        #     # 2. 분석 결과 블록 생성
        #     blocks = format_participation_blocks(participation_scores, analysis_type)

        #     blocks.append(
        #         {
        #             "type": "image",
        #             "image_url": file_url,
        #             "alt_text": "참여도 분석 결과"
        #         }
        #     )

        #     # 3. 분석 결과 메시지 전송
        #     client.chat_postMessage(
        #         channel=channel_id,
        #         blocks=blocks,
        #         text="참여도 분석 결과입니다!"  # 기본 텍스트 추가
        #     )
        # else:
        #     client.chat_postMessage(
        #         channel=channel_id,
        #         text="앗! 결과를 업로드하는 중에 문제가 발생했어요."
        #     )
    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        client.chat_postMessage(
            channel=channel_id,
            text="앗! Slack API 오류가 발생했어요."
        )
    except Exception as e:
        print(f"Error in handle_participation_analysis: {e}")
        client.chat_postMessage(
            channel=channel_id,
            text="앗! 참여도 분석 중 문제가 발생했어요."
        )

# 참여도 분석 명령어 처리 라우트 (발화량)
@app.route('/participation_speech', methods=['POST'])
def participation_speech():
    slack_event = request.form.copy()
    channel_id = slack_event.get('channel_id')

    threading.Thread(target=handle_participation_analysis, args=(channel_id, 'speech_amount')).start()

    return make_response("발화량 참여도 분석을 시작합니다.", 200)

# 참여도 분석 명령어 처리 라우트 (메시지 수)
@app.route('/participation_message', methods=['POST'])
def participation_message():
    slack_event = request.form.copy()
    channel_id = slack_event.get('channel_id')

    threading.Thread(target=handle_participation_analysis, args=(channel_id, 'message_count')).start()

    return make_response("메시지 수 참여도 분석을 시작합니다.", 200)

# 참여도 분석 명령어 처리 라우트 (반응 수)
@app.route('/participation_reaction', methods=['POST'])
def participation_reaction():
    slack_event = request.form.copy()
    channel_id = slack_event.get('channel_id')

    threading.Thread(target=handle_participation_analysis, args=(channel_id, 'reaction_count')).start()

    return make_response("반응 수 참여도 분석을 시작합니다.", 200)

# 채팅 로그 전처리 함수
def preprocess_chat_logs(chat_logs):
    preprocessed_text = []
    indexed_chat_logs = []
    texts = []

    for idx, log in enumerate(chat_logs):
        user_id = log['user_id']
        username = log['username']
        text = log['text']

        # 인덱스와 사용자명 포함한 텍스트 생성
        preprocessed_text.append(f"{idx}: <@{username}>: {text}")

        # 인덱스가 포함된 채팅 로그 생성
        indexed_chat_logs.append({
            'index': idx,
            'user_id': user_id,
            'username': username,
            'text': text
        })

        texts.append(text)

    return "\n".join(preprocessed_text), indexed_chat_logs, texts

# LLM을 사용하여 주제 추출 함수
def extract_topic(full_meeting_text):
    prompt_text = """
    당신은 주제 추출 전문가입니다.

    다음은 회의의 전체 대화 내용입니다:
    '{full_meeting_text}'

    이 회의의 주요 주제를 하나의 명사구로 10자 이내로 요약해주세요.
    예시: '제품 출시 계획', '예산 절감 방안'
    응답은 오직 주제만 작성하고, 다른 불필요한 말은 하지 마세요.
    """

    prompt = prompt_text.format(full_meeting_text=full_meeting_text)

    try:
        topic = watsonx_llm.invoke(prompt)
        topic = topic.strip()
        topic = topic.split('|')[0]  # '|' 문자가 있다면 그 앞부분만 사용

        print(f"LLM 응답: {topic}")
        return topic
    except Exception as e:
        print(f"Error extracting topic: {e}")
        return "주제 추출 실패"

# 임베딩 생성 함수
def get_embeddings(text_list):
    embeddings = embedding_model.embed_documents(texts=text_list)
    embeddings = np.array(embeddings)
    return embeddings

# 유사도 계산 함수
def calculate_similarity(embedding1, embedding2):
    embedding1 = np.array(embedding1).reshape(1, -1)
    embedding2 = np.array(embedding2).reshape(1, -1)
    return cosine_similarity(embedding1, embedding2)[0][0]

# 유사도 점수 통계치 계산 함수
def calculate_similarity_statistics(similarity_scores):
    max_score = np.max(similarity_scores)
    min_score = np.min(similarity_scores)
    mean_score = np.mean(similarity_scores)
    median_score = np.median(similarity_scores)
    std_dev = np.std(similarity_scores)
    percentiles = np.percentile(similarity_scores, [25, 50, 75, 90, 95])

    print("유사도 점수 통계치:")
    print(f"최대값: {max_score:.4f}")
    print(f"최소값: {min_score:.4f}")
    print(f"평균값: {mean_score:.4f}")
    print(f"중앙값: {median_score:.4f}")
    print(f"표준편차: {std_dev:.4f}")
    print(f"백분위수 (25%, 50%, 75%, 90%, 95%): {percentiles}")

    return {
        'max': max_score,
        'min': min_score,
        'mean': mean_score,
        'median': median_score,
        'std_dev': std_dev,
        'percentiles': percentiles
    }

# 유사도 점수 분포 시각화 함수
def plot_similarity_distribution(similarity_scores, threshold):
    set_korean_font()  # 한글 폰트 설정

    plt.figure(figsize=(10, 6))
    sns.histplot(similarity_scores, bins=30, kde=True, color='skyblue')
    plt.title('유사도 점수 분포', loc='left', fontsize=20)
    plt.xlabel('유사도 점수')
    plt.ylabel('빈도수')

    # threshold 위치에 세로선 추가
    plt.axvline(x=threshold, color="red", linestyle="--", label=f"Threshold ({threshold:.2f})")

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close()

    return img_buf

# 클러스터별 최소값과 최대값 계산 함수
def get_cluster_min_max(similarity_scores, labels):
    cluster_0_scores = similarity_scores[labels == 0]
    cluster_1_scores = similarity_scores[labels == 1]

    cluster_0_min = np.min(cluster_0_scores)
    cluster_0_max = np.max(cluster_0_scores)
    cluster_1_min = np.min(cluster_1_scores)
    cluster_1_max = np.max(cluster_1_scores)

    return {
        'cluster_0': {'min': cluster_0_min, 'max': cluster_0_max},
        'cluster_1': {'min': cluster_1_min, 'max': cluster_1_max}
    }

# 임계값 계산 함수
def determine_threshold_with_cluster_extremes(cluster_min_max, kmeans):
    # 클러스터 중심점 확인
    cluster_0_centroid = kmeans.cluster_centers_[0][0]
    cluster_1_centroid = kmeans.cluster_centers_[1][0]

    if cluster_0_centroid > cluster_1_centroid:
        topic_cluster = 0
        non_topic_cluster = 1
    else:
        topic_cluster = 1
        non_topic_cluster = 0

    # 주제 관련 클러스터의 최소값과 비관련 클러스터의 최대값
    topic_cluster_min = cluster_min_max[f'cluster_{topic_cluster}']['min']
    non_topic_cluster_max = cluster_min_max[f'cluster_{non_topic_cluster}']['max']

    # 임계값 계산
    threshold = (topic_cluster_min + non_topic_cluster_max) / 2
    print(f"주제 관련 클러스터 최소값: {topic_cluster_min:.4f}")
    print(f"비관련 클러스터 최대값: {non_topic_cluster_max:.4f}")
    print(f"설정된 임계값 (두 값의 중간값): {threshold:.4f}")

    return threshold, topic_cluster

# 주제 관련 발언 비율 계산 함수
def calculate_high_similarity_ratio_with_threshold(indexed_chat_logs, similarity_scores, threshold):
    user_high_similarity = {}

    for i, log in enumerate(indexed_chat_logs):
        user_id = log['user_id']
        username = log['username']
        similarity_score = similarity_scores[i]

        if user_id not in user_high_similarity:
            user_high_similarity[user_id] = {'username': username, 'high_similarity_count': 0, 'message_count': 0}
        if similarity_score >= threshold:
            user_high_similarity[user_id]['high_similarity_count'] += 1
        user_high_similarity[user_id]['message_count'] += 1

    # 비율 계산
    for user_id in user_high_similarity:
        user_high_similarity[user_id]['high_similarity_ratio'] = (
            user_high_similarity[user_id]['high_similarity_count'] / user_high_similarity[user_id]['message_count']
        )

    return user_high_similarity

# 주제 관련 발언 비율 차트 생성 함수
def create_high_similarity_chart(sorted_high_similarity_scores):
    set_korean_font()  # 한글 폰트 설정

    # sorted_high_similarity_scores는 리스트 형태의 튜플 (user_id, info_dict)
    usernames = [info['username'] for _, info in sorted_high_similarity_scores]
    high_similarity_ratios = [info['high_similarity_ratio'] for _, info in sorted_high_similarity_scores]

    # 색상 리스트
    colors = ['gold', 'lightcoral', 'lightskyblue']

    # 바 차트 생성
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.bar(usernames, high_similarity_ratios, color=colors)
    ax.set_title('주제 관련 발언 비율', loc='left', fontsize=20)
    ax.set_ylabel('비율')

    plt.tight_layout()

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close()

    return img_buf

# 주제 유사도 분석 실행 함수
def perform_topic_relevance_analysis(chat_logs):
    # 채팅 로그 전처리
    full_meeting_text, indexed_chat_logs, texts = preprocess_chat_logs(chat_logs)

    # 주제 추출
    extracted_topic = extract_topic(full_meeting_text)
    print(f"추출된 주제: {extracted_topic}")

    # 임베딩 계산
    topic_embedding = get_embeddings([extracted_topic])[0]
    text_embeddings = get_embeddings(texts)

    # 유사도 점수 계산
    similarity_scores = []
    for text_embedding in text_embeddings:
        similarity = calculate_similarity(topic_embedding, text_embedding)
        similarity_scores.append(similarity)
    similarity_scores = np.array(similarity_scores)

    # 통계치 계산
    statistics = calculate_similarity_statistics(similarity_scores)

    # K-평균 클러스터링 수행
    scores_reshaped = similarity_scores.reshape(-1, 1)
    kmeans = KMeans(n_clusters=2, random_state=0).fit(scores_reshaped)
    labels = kmeans.labels_

    # 클러스터별 최소값과 최대값 계산
    cluster_min_max = get_cluster_min_max(similarity_scores, labels)

    # 임계값 계산
    threshold, topic_cluster = determine_threshold_with_cluster_extremes(cluster_min_max, kmeans)

    # 주제 관련 발언 비율 계산
    high_similarity_scores = calculate_high_similarity_ratio_with_threshold(
        indexed_chat_logs, similarity_scores, threshold
    )

    # 값을 기준으로 내림차순 정렬
    sorted_high_similarity_scores = sorted(high_similarity_scores.items(), key=lambda x: x[1]['high_similarity_ratio'], reverse=True)

    # MVP 선정 (리스트가 비어있지 않은지 확인)
    if sorted_high_similarity_scores:
        mvp_user_id, mvp_info = sorted_high_similarity_scores[0]
        mvp_user = mvp_info['username']
    else:
        mvp_user = "없음"

    # 주제 관련 발언 비율 차트 생성
    chart_buf = create_high_similarity_chart(sorted_high_similarity_scores)

    # 유사도 분포
    similarity_distribution = plot_similarity_distribution(similarity_scores, threshold)

    return sorted_high_similarity_scores, chart_buf, extracted_topic, statistics, similarity_distribution, threshold, mvp_user

# 주제 유사도 분석 명령어 처리 라우트
@app.route('/topic_relevance', methods=['POST'])
def topic_relevance():
    slack_event = request.form.copy()
    channel_id = slack_event.get('channel_id')
    user_id = slack_event.get('user_id')

    threading.Thread(target=handle_topic_relevance, args=(channel_id, user_id)).start()

    return make_response("주제 유사도 분석을 시작합니다.", 200)

# 주제 유사도 분석 함수
def handle_topic_relevance(channel_id, user_id):
    try:
        # 채팅 로그 가져오기
        chat_logs = get_chatlog(channel_id)
        if not chat_logs:
            client.chat_postMessage(
                channel=channel_id,
                text="앗! 채팅 로그를 가져오는 중 문제가 발생했어요."
            )
            return

        MODEL_NAME = 'llama3-70b'

        watsonx_llm = WatsonxLLM(
            model_id=MODEL_ID_list[MODEL_NAME],
            url="https://us-south.ml.cloud.ibm.com",
            project_id=PROJECT_ID,
            params=parameters,
        )

        # 주제 유사도 분석 실행
        (
            sorted_high_similarity_scores, topic_chart_buf, extracted_topic,
            statistics, similarity_distribution, threshold, mvp_user
        ) = perform_topic_relevance_analysis(chat_logs)

        # 블록 생성 함수 호출
        blocks = format_topic_relevance_blocks(extracted_topic, statistics, threshold, mvp_user)

        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text="주제 유사도 분석 결과입니다!"
        )

        # 유사도 분포 차트 이미지 업로드
        dsitribution_chart_upload = client.files_upload_v2(
            channel=channel_id,
            file=similarity_distribution,
            filename='similarity_distribution.png',
            title='유사도 분포 시각화'
        )

        # 결과 이미지 업로드
        topic_chart_upload = client.files_upload_v2(
            channel=channel_id,
            file=topic_chart_buf,
            filename='topic_relevance_analysis.png',
            title='주제 유사도 분석 결과'
        )

        # if topic_chart_upload['ok']:
        #     topic_file_info = topic_chart_upload['file']
        #     topic_file_url = topic_file_info.get('permalink_public')

        #     # 블록 생성 함수 호출
        #     blocks = format_topic_relevance_blocks(extracted_topic, statistics, topic_file_url)

        #     client.chat_postMessage(
        #         channel=channel_id,
        #         blocks=blocks,
        #         text="주제 유사도 분석 결과입니다!"
        #     )
        # else:
        #     client.chat_postMessage(
        #         channel=channel_id,
        #         text="앗! 결과를 업로드하는 중에 문제가 발생했어요."
        #     )
    except Exception as e:
        print(f"Error in handle_topic_relevance: {e}")
        client.chat_postMessage(
            channel=channel_id,
            text="앗! 주제 유사도 분석 중 문제가 발생했어요."
        )


def format_topic_relevance_blocks(extracted_topic, statistics, threshold, mvp_user):
    statistics_block = {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": f"*최대값:* {statistics['max']:.4f}"
            },
            {
                "type": "mrkdwn",
                "text": f"*최소값:* {statistics['min']:.4f}"
            },
            {
                "type": "mrkdwn",
                "text": f"*평균값:* {statistics['mean']:.4f}"
            },
            {
                "type": "mrkdwn",
                "text": f"*중앙값:* {statistics['median']:.4f}"
            },
            {
                "type": "mrkdwn",
                "text": f"*표준편차:* {statistics['std_dev']:.4f}"
            },
            {
                "type": "mrkdwn",
                "text": f"*클러스터 임계값:* {threshold:.4f}"
            }
        ]
    }

    # MVP 메시지
    mvp_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*:crown: 참여도 MVP는 *{mvp_user}* 님입니다! 정말 대단해요! :tada:"
        }
    }

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*주제 유사도 분석 결과입니다!* :sparkles:\n추출된 주제: *{extracted_topic}*"
            }
        },
        statistics_block,
        {"type": "divider"},
        mvp_block
        # {
        #     "type": "image",
        #     "image_url": topic_file_url,
        #     "alt_text": "주제 유사도 분석 그래프"
        # }
    ]
    return blocks



# 개별 발언 평가 함수
def evaluate_single_utterance_with_llm(log):
    utterance_text = f"{log['index']}: <@{log['username']}>: {log['text']}"

    prompt_text = f"""
    발언: '{utterance_text}'

    위 발언에 대해 다음 네 가지 기준으로 1~5점 척도로 평가하세요:
    1. 토론 유도 및 다른 팀원 발언 촉진
    2. 회의 방향 설정 및 결론 도출 기여
    3. 회의 목표 달성에 대한 기여
    4. 협업 촉진 및 의견 차이 좁히기

    형식:
    [토론 유도 점수, 회의 방향 점수, 목표 달성 점수, 협업 촉진 점수]

    응답은 위의 형식으로만 작성하고, 추가 설명은 하지 마세요.
    """

    prompt = prompt_text

    try:
        response = watsonx_llm.invoke(prompt)
        print(f"인덱스 {log['index']}의 응답:\n{response}\n")
        pattern = re.compile(r'\[(\d+),\s*(\d+),\s*(\d+),\s*(\d+)\]')
        match = pattern.search(response.strip())
        if match:
            scores = [int(match.group(i)) for i in range(1, 5)]
            evaluation_result = {
                'index': log['index'],
                'user_id': log['user_id'],
                'username': log['username'],
                'discussion': scores[0],
                'direction': scores[1],
                'goal': scores[2],
                'collaboration': scores[3]
            }
            return evaluation_result
        else:
            print(f"응답에서 점수를 추출하지 못했습니다. 인덱스 {log['index']}")
            return None
    except Exception as e:
        print(f"LLM 호출 중 오류 발생 (인덱스 {log['index']}): {e}")
        return None

# 사용자별 기여도 점수 집계 함수
def aggregate_contribution_scores(indexed_chat_logs, evaluation_results):
    contribution_scores = {}
    for eval_result in evaluation_results:
        user_id = eval_result['user_id']
        username = eval_result['username']
        if user_id not in contribution_scores:
            contribution_scores[user_id] = {
                'username': username,
                'discussion': 0,
                'direction': 0,
                'goal': 0,
                'collaboration': 0
            }
        contribution_scores[user_id]['discussion'] += eval_result['discussion']
        contribution_scores[user_id]['direction'] += eval_result['direction']
        contribution_scores[user_id]['goal'] += eval_result['goal']
        contribution_scores[user_id]['collaboration'] += eval_result['collaboration']
    return contribution_scores

# 기여도 차트 생성 함수
def create_contribution_chart(contribution_scores):
    set_korean_font()  # 한글 폰트 설정

    usernames = [scores['username'] for scores in contribution_scores.values()]
    discussion_scores = [scores['discussion'] for scores in contribution_scores.values()]
    direction_scores = [scores['direction'] for scores in contribution_scores.values()]
    goal_scores = [scores['goal'] for scores in contribution_scores.values()]
    collaboration_scores = [scores['collaboration'] for scores in contribution_scores.values()]

    x = np.arange(len(usernames))
    width = 0.2

    colors = ['yellowgreen', 'gold', 'lightskyblue', 'lightcoral']

    plt.figure(figsize=(12, 6))
    plt.bar(x - width*1.5, discussion_scores, width=width, label='토론 유도', color=colors[0])
    plt.bar(x - width*0.5, direction_scores, width=width, label='회의 방향', color=colors[1])
    plt.bar(x + width*0.5, goal_scores, width=width, label='목표 달성', color=colors[2])
    plt.bar(x + width*1.5, collaboration_scores, width=width, label='협업 촉진', color=colors[3])

    plt.xticks(x, usernames)
    plt.xlabel('사용자')
    plt.ylabel('점수 합계')
    plt.title('사용자별 회의 기여도 분석', loc='left', fontsize=20)
    plt.legend()
    plt.tight_layout()

    img_buf = io.BytesIO()
    plt.savefig(img_buf, format='png')
    img_buf.seek(0)
    plt.close()

    return img_buf

# 회의 기여도 분석 실행 함수
def perform_contribution_analysis(chat_logs):
    # 채팅 로그 전처리
    _, indexed_chat_logs, _ = preprocess_chat_logs(chat_logs)

    all_evaluation_results = []
    for log in indexed_chat_logs:
        evaluation_result = evaluate_single_utterance_with_llm(log)
        if evaluation_result:
            all_evaluation_results.append(evaluation_result)
        else:
            continue

    # 사용자별 기여도 점수 집계
    contribution_scores = aggregate_contribution_scores(indexed_chat_logs, all_evaluation_results)

    # 기여도 차트 생성
    chart_buf = create_contribution_chart(contribution_scores)

    return contribution_scores, chart_buf

# 회의 기여도 분석 명령어 처리 라우트
@app.route('/contribution_analysis', methods=['POST'])
def contribution_analysis():
    slack_event = request.form.copy()
    channel_id = slack_event.get('channel_id')
    user_id = slack_event.get('user_id')

    threading.Thread(target=handle_contribution_analysis, args=(channel_id, user_id)).start()

    return make_response("회의 기여도 분석을 시작합니다.", 200)

# 회의 진행 기여도 분석 함수
def handle_contribution_analysis(channel_id, user_id):
    try:
        # 채팅 로그 가져오기
        chat_logs = get_chatlog(channel_id)
        if not chat_logs:
            client.chat_postMessage(
                channel=channel_id,
                text="앗! 채팅 로그를 가져오는 중 문제가 발생했어요."
            )
            return

        MODEL_NAME = 'llama3-8b'

        watsonx_llm = WatsonxLLM(
            model_id=MODEL_ID_list[MODEL_NAME],
            url="https://us-south.ml.cloud.ibm.com",
            project_id=PROJECT_ID,
            params=parameters,
        )

        # 회의 기여도 분석 실행
        contribution_scores, contribution_chart_buf = perform_contribution_analysis(chat_logs)

        # 결과 이미지 업로드
        contribution_chart_upload = client.files_upload_v2(
            channel=channel_id,
            file=contribution_chart_buf,
            filename='contribution_analysis.png',
            title='회의 기여도 분석 결과'
        )

        # 분석 결과 블록 생성
        blocks = format_contribution_blocks(contribution_scores)

        # 분석 결과 메시지 전송
        client.chat_postMessage(
            channel=channel_id,
            blocks=blocks,
            text="회의 기여도 분석 결과입니다!"
        )

        # if contribution_chart_upload['ok']:
        #     # 업로드된 파일의 정보
        #     contribution_file_info = contribution_chart_upload['file']
        #     contribution_file_url = contribution_file_info.get('permalink_public')  # 공개 URL 확보

        #     if not contribution_file_url:
        #         # permalink_public이 없는 경우
        #         client.chat_postMessage(
        #             channel=channel_id,
        #             text="앗! 이미지를 공개적으로 공유하는 데 문제가 발생했어요."
        #         )
        #         return

        #     # 분석 결과 블록 생성
        #     blocks = format_contribution_blocks(contribution_scores)

        #     blocks.append(
        #         {
        #             "type": "image",
        #             "image_url": contribution_file_url,
        #             "alt_text": "회의 기여도 분석 그래프"
        #         }
        #     )

        #     # 분석 결과 메시지 전송
        #     client.chat_postMessage(
        #         channel=channel_id,
        #         blocks=blocks,
        #         text="회의 기여도 분석 결과입니다!"
        #     )
        # else:
        #     client.chat_postMessage(
        #         channel=channel_id,
        #         text="앗! 이미지를 업로드하는 중에 문제가 발생했어요."
        #     )
    except SlackApiError as e:
        print(f"Slack API error: {e.response['error']}")
        client.chat_postMessage(
            channel=channel_id,
            text="앗! Slack API 오류가 발생했어요."
        )
    except Exception as e:
        print(f"Error in handle_contribution_analysis: {e}")
        client.chat_postMessage(
            channel=channel_id,
            text="앗! 회의 기여도 분석 중 문제가 발생했어요."
        )

def format_contribution_blocks(contribution_scores):
    # 사용자별 점수 리스트 생성 및 총합 계산
    user_list = []
    for user_id, scores in contribution_scores.items():
        total_sum = scores['discussion'] + scores['direction'] + scores['goal'] + scores['collaboration']
        user_list.append((user_id, scores, total_sum))

    # 총합 기준으로 내림차순 정렬
    sorted_user_list = sorted(user_list, key=lambda x: x[2], reverse=True)

    if not sorted_user_list:
        # 사용자 데이터가 없는 경우
        return []

    # 팀장 추천 (가장 높은 합계를 가진 사용자)
    top_user = sorted_user_list[0][1]  # scores dict
    top_user_id = sorted_user_list[0][0]
    top_user_sum = sorted_user_list[0][2]

    leader_block = {
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": f"*팀장 추천:* <@{top_user_id}> ({top_user['username']}) 님!\n덕분에 우리 팀이 데굴데굴 잘 굴러가요! 🐢💨\n총 점수: {top_user_sum}점 🥇"
        }
    }

    # 사용자별 점수 블록 생성 (정렬된 순서대로)
    user_blocks = []
    for user_id, scores, total_sum in sorted_user_list:
        text = (
            f"*{scores['username']}* 님:\n"
            f"• 토론 유도: {scores['discussion']}점\n"
            f"• 회의 방향: {scores['direction']}점\n"
            f"• 목표 달성: {scores['goal']}점\n"
            f"• 협업 촉진: {scores['collaboration']}점\n"
            f"• 총 점수: {total_sum}점"
        )
        user_blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": text
            }
        })
        user_blocks.append({"type": "divider"})

    # 전체 통계 계산
    total_discussion = sum(scores['discussion'] for scores in contribution_scores.values())
    total_direction = sum(scores['direction'] for scores in contribution_scores.values())
    total_goal = sum(scores['goal'] for scores in contribution_scores.values())
    total_collaboration = sum(scores['collaboration'] for scores in contribution_scores.values())
    user_count = len(contribution_scores)
    average_discussion = total_discussion / user_count if user_count > 0 else 0
    average_direction = total_direction / user_count if user_count > 0 else 0
    average_goal = total_goal / user_count if user_count > 0 else 0
    average_collaboration = total_collaboration / user_count if user_count > 0 else 0

    # 전체 통계 블록 생성
    stats_block = {
        "type": "section",
        "fields": [
            {
                "type": "mrkdwn",
                "text": f"*총 토론 유도 점수:* {total_discussion}점"
            },
            {
                "type": "mrkdwn",
                "text": f"*평균 토론 유도 점수:* {average_discussion:.2f}점"
            },
            {
                "type": "mrkdwn",
                "text": f"*총 회의 방향 점수:* {total_direction}점"
            },
            {
                "type": "mrkdwn",
                "text": f"*평균 회의 방향 점수:* {average_direction:.2f}점"
            },
            {
                "type": "mrkdwn",
                "text": f"*총 목표 달성 점수:* {total_goal}점"
            },
            {
                "type": "mrkdwn",
                "text": f"*평균 목표 달성 점수:* {average_goal:.2f}점"
            },
            {
                "type": "mrkdwn",
                "text": f"*총 협업 촉진 점수:* {total_collaboration}점"
            },
            {
                "type": "mrkdwn",
                "text": f"*평균 협업 촉진 점수:* {average_collaboration:.2f}점"
            }
        ]
    }

    # 블록 리스트 생성
    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*회의 기여도 분석 결과입니다!* :sparkles:"
            }
        },
        {"type": "divider"},
        stats_block,
        {"type": "divider"},
        leader_block,
        {"type": "divider"}
    ]

    # 사용자별 점수 블록 추가
    blocks.extend(user_blocks)

    return blocks


# 메인 실행 부분
if __name__ == '__main__':
    app.run(debug=True)
