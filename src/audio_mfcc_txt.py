from flask import Flask, request
import wave
import os
import librosa
import numpy as np
from datetime import datetime
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)

# 데이터베이스 연결 설정
db_config = {
    'host': 'ssu-info.civydey9zqjl.us-east-2.rds.amazonaws.com',
    'user': 'admin',
    'password': 'reapinjoy',
    'database': 'ssu_info'
}

def save_mfcc_to_db(file_name, mfcc_data): # 데이터베이스에 MFCC 데이터를 저장하는 함수
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            cursor = connection.cursor()
            # 데이터베이스에 데이터 삽입
            query = "INSERT INTO audio_mfcc (file_name, mfcc_data) VALUES (%s, %s)"
            cursor.execute(query, (file_name, mfcc_data))
            connection.commit()
            print(f"MFCC data successfully saved to database for file {file_name}.")
    except Error as e:
        print(f"Error while connecting to MySQL: {e}")
    finally:
        if connection.is_connected(): # 데이터베이스 연결 오류 발생 시
            cursor.close()
            connection.close()

@app.route('/upload', methods=['POST'])
def upload_data():
    # 클라이언트로부터 오디오 데이터를 받아 처리
    try:
        # 이 부분에서 request.data를 사용하여 바이너리 데이터를 직접 얻음
        audio_data = request.data
        if not audio_data:
            raise ValueError("No audio data received") # 오디오 데이터가 없으면 에러 발생

        wav_output_file = find_next_output_filename('.wav')
        mfcc_output_file = find_next_output_filename('.txt')

        sample_rate = 8000
        num_channels = 1
        sample_width = 2

        # WAV 파일로 오디오 데이터 저장
        with wave.open(wav_output_file, 'wb') as wav_file:
            wav_file.setnchannels(num_channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_data)
        print(f"WAV file {wav_output_file} has been created.")

        # MFCC 추출
        data, sr = librosa.load(wav_output_file, sr=sample_rate)
        mfccs = librosa.feature.mfcc(y=data, sr=sr, n_mfcc=13)
        mfccs_processed = np.mean(mfccs.T, axis=0)

        # TXT 파일로 MFCC 데이터 저장
        np.savetxt(mfcc_output_file, mfccs_processed)
        print(f"TXT file {mfcc_output_file} containing MFCC data has been created.")

        # 데이터베이스에 MFCC 데이터 저장
        save_mfcc_to_db(wav_output_file, mfccs_processed.tolist())

        return 'Data received and MFCC extracted'

    except ValueError as e:
        return f'Error: {e}', 400 # 잘못된 값 에러 처리
    except Exception as e:
        return f'An error occurred: {e}', 500 # 기타 예외 처리

def find_next_output_filename(extension): # 파일명 생성을 위한 함수
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S") # 현재 시간으로 타임스탬프 생성
    base_filename = 'output'
    output_file = f'{base_filename}_{timestamp}{extension}'
    count = 1
    while os.path.isfile(output_file): # 동일한 이름이 존재하지 않을 때까지 파일명 수정
        output_file = f'{base_filename}_{timestamp}_{count}{extension}'
        count += 1
    return output_file

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)  # 디버그 모드 활성화
