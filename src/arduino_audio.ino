#include <WiFi.h>
#include <HTTPClient.h>

const char* ssid = "KT_GiGA_2G_AD64";
const char* password = "7bea5zz759";
const char* serverUrl = "http://172.30.1.9:5000/upload";

const int sampleRate = 8000;
const int sampleSize = 2;
const int bufferSize = 256; // 한 번에 전송할 데이터 크기
uint8_t buffer[bufferSize];

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
}

void loop() {
  if(WiFi.status() == WL_CONNECTED) {
    HTTPClient http;
    http.begin(serverUrl);
    http.addHeader("Content-Type", "application/octet-stream");

    unsigned long startTime = millis();
    while (millis() - startTime < 10000) { // 10초간 데이터 수집
      for (int i = 0; i < bufferSize; i += sampleSize) {
        int sensorValue = analogRead(34);
        buffer[i] = sensorValue & 0xFF;
        buffer[i + 1] = (sensorValue >> 8) & 0xFF;
        delayMicroseconds(125); // 샘플링 속도 유지
      }

      http.POST(buffer, bufferSize); // 버퍼 크기만큼 데이터 전송
    }

    Serial.println("Data transmission complete."); // 데이터 전송 완료 메시지

    http.end();
    delay(10000); // 10초 대기 후 다시 시작

    Serial.println("Waiting for next data collection..."); // 대기중 메시지
  }
  else {
    Serial.println("Error in WiFi connection");
  }
}