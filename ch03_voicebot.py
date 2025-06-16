import streamlit as st
from audiorecorder import audiorecorder
import openai
import os
from datetime import datetimeg
from gtts import gTTS
import base64

# 텍스트 음성 변환
def TTS(response):
    filename = 'output.mp3'
    tts = gTTS(text=response, lang='ko')
    tts.save(filename)
    
    with open(filename, 'rb') as f:
        data = f.read()
        b64 = base64.b64encode(data).decode()
        md = f'''
        <audio autoplay="true">
        <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        '''
        st.markdown(md, unsafe_allow_html=True)
    os.remove(filename)

# 음성 텍스트 변환
def STT(audio, apikey):
    filename = 'input.mp3'
    audio.export(filename, format='mp3')
    
    with open(filename, 'rb') as audio_file:
        client = openai.OpenAI(api_key=apikey)
        response = client.audio.transcriptions.create(
            model='whisper-1',
            file=audio_file
        )
    os.remove(filename)
    return response.text

# GPT 응답
def ask_gpt(prompt, model, apikey):
    client = openai.OpenAI(api_key=apikey)
    response = client.chat.completions.create(
        model=model,
        messages=prompt
    )
    return response.choices[0].message.content

# 메인 앱
def main():
    st.set_page_config(page_title='음성 비서 프로그램', layout='wide')
    st.header('🗣️ 음성 비서 프로그램')
    st.markdown('---')

    with st.expander('📌 프로그램 설명', expanded=True):
        st.write('''
        - UI는 Streamlit을 사용했습니다.
        - STT는 OpenAI Whisper API를 사용했습니다.
        - GPT 모델은 ChatGPT를 기반으로 합니다.
        - TTS는 Google Text-to-Speech를 사용했습니다.
        ''')

    # 상태 초기화
    if 'chat' not in st.session_state:
        st.session_state['chat'] = []

    if 'OPENAI_API' not in st.session_state:
        st.session_state['OPENAI_API'] = ''

    if 'messages' not in st.session_state:
        st.session_state['messages'] = [
            {"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korean."}
        ]

    if 'check_reset' not in st.session_state:
        st.session_state['check_reset'] = False

    # 사이드바
    with st.sidebar:
        st.session_state['OPENAI_API'] = st.text_input(
            label='🔑 OPENAI API 키',
            placeholder='Enter your API key',
            value='',
            type='password'
        )

        model = st.radio(label='🧠 GPT 모델 선택', options=['gpt-4', 'gpt-3.5-turbo'])

        if st.button(label='🔁 초기화'):
            st.session_state['chat'] = []
            st.session_state['messages'] = [
                {"role": "system", "content": "You are a thoughtful assistant. Respond to all input in 25 words and answer in korean."}
            ]
            st.session_state['check_reset'] = True

    # 인터페이스
    col1, col2 = st.columns(2)

    with col1:
        st.subheader('🎙️ 질문하기')
        audio = audiorecorder('클릭하여 녹음하기', '녹음 중...')
        if audio.duration_seconds > 0 and not st.session_state['check_reset']:
            st.audio(audio.export().read())
            question = STT(audio, st.session_state['OPENAI_API'])

            now = datetime.now().strftime('%H:%M')
            st.session_state['chat'].append(('user', now, question))
            st.session_state['messages'].append({"role": "user", "content": question})

    with col2:
        st.subheader('💬 질문/답변')
        if audio.duration_seconds > 0 and not st.session_state['check_reset']:
            response = ask_gpt(st.session_state['messages'], model, st.session_state['OPENAI_API'])
            now = datetime.now().strftime('%H:%M')

            st.session_state['chat'].append(('bot', now, response))
            st.session_state['messages'].append({"role": "assistant", "content": response})

            for sender, time, message in st.session_state['chat']:
                if sender == 'user':
                    st.markdown(
                        f'<div style="display:flex;align-items:center;">'
                        f'<div style="background-color:#007AFF;color:white;border-radius:12px;padding:8px 12px;margin-right:8px;">{message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div>'
                        f'</div>', unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;justify-content:flex-end;">'
                        f'<div style="background-color:lightgray;border-radius:12px;padding:8px 12px;margin-left:8px;">{message}</div>'
                        f'<div style="font-size:0.8rem;color:gray;">{time}</div>'
                        f'</div>', unsafe_allow_html=True
                    )

            TTS(response)

if __name__ == "__main__":
    main()