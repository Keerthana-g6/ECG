/* esp32/ecg_stream.ino
   Dual input: AD8232 electrode (ADC) OR DAC simulation (ADC loopback)
   Sends 1000-sample JSON windows to backend /predict
*/
#include <WiFi.h>
#include <HTTPClient.h>
#include <WebSocketsServer.h>

const char* WIFI_SSID = "YOUR_SSID";
const char* WIFI_PASS = "YOUR_PASS";
const char* BACKEND_URL = "http://192.168.x.y:5000/predict";

#define ECG_ADC_PIN 34
#define BUTTON_PIN 14
bool useDAC = false;

WebSocketsServer webSocket = WebSocketsServer(81);
const int WINDOW_LEN = 1000;
float bufferData[WINDOW_LEN];
int bufIndex = 0;

void IRAM_ATTR handleButton() {
  useDAC = !useDAC;
}

void setup(){
  Serial.begin(115200);
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(BUTTON_PIN, handleButton, FALLING);
  analogReadResolution(12);
  analogSetPinAttenuation(ECG_ADC_PIN, ADC_11db);

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting WiFi");
  unsigned long start=millis();
  while(WiFi.status()!=WL_CONNECTED && millis()-start<20000){
    Serial.print("."); delay(300);
  }
  if(WiFi.status()==WL_CONNECTED) Serial.println(WiFi.localIP()); else Serial.println("WiFi failed");
  webSocket.begin();
  webSocket.onEvent([](uint8_t num, WStype_t type, uint8_t * payload, size_t length){});
}

float adc_to_volt(int raw){
  float v = (float)raw / 4095.0f;
  v = (v - 0.5f) * 2.0f;
  return v;
}

void sendWindow(float *win, int len){
  if(WiFi.status()!=WL_CONNECTED) return;
  HTTPClient http; http.begin(BACKEND_URL); http.addHeader("Content-Type","application/json");
  String payload = "{\"ecg\":[";
  for(int i=0;i<len;i++){ payload += String(win[i],6); if(i<len-1) payload += ","; }
  payload += "], \"fs\":200 }";
  int code = http.POST(payload);
  if(code>0) Serial.printf("POST %d\\n", code);
  else Serial.printf("POST failed %s\\n", http.errorToString(code).c_str());
  http.end();
}

void loop(){
  webSocket.loop();
  int raw = analogRead(ECG_ADC_PIN);
  float sample = adc_to_volt(raw);
  bufferData[bufIndex++] = sample;
  if(bufIndex>=WINDOW_LEN){
    sendWindow(bufferData, WINDOW_LEN);
    bufIndex = 0;
  }
  webSocket.broadcastTXT(String(sample,6));
  delayMicroseconds(5000); // ~200Hz
}
