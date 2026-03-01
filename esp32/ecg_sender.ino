#include <WiFi.h>
#include <HTTPClient.h>

// 1. CHANGE THESE
const char* ssid     = "YOUR_WIFI_NAME";
const char* password = "YOUR_WIFI_PASSWORD";

// 2. CHANGE THIS IP TO YOUR LAPTOP IP (you saw 192.168.29.230 in logs)
String serverUrl = "http://192.168.29.230:5000/infer";

// ECG analog input pin
const int ECG_PIN = 34;   // use the pin you wired sensor output to

// buffer for 1000 samples (~5 sec at 200 Hz)
const int N_SAMPLES = 1000;
int ecgBuffer[N_SAMPLES];
int idx = 0;

void setup() {
  Serial.begin(115200);
  delay(1000);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: ");
  Serial.println(WiFi.localIP());

  analogReadResolution(12); // 0–4095
}

void loop() {
  int raw = analogRead(ECG_PIN);
  ecgBuffer[idx++] = raw;

  if (idx >= N_SAMPLES) {
    idx = 0;

    if (WiFi.status() == WL_CONNECTED) {
      HTTPClient http;
      http.begin(serverUrl);
      http.addHeader("Content-Type", "application/json");

      // build JSON array
      String payload = "{\"ecg\":[";
      for (int i = 0; i < N_SAMPLES; i++) {
        payload += String(ecgBuffer[i]);
        if (i < N_SAMPLES - 1) payload += ",";
      }
      payload += "]}";

      int code = http.POST(payload);
      Serial.print("POST /infer -> HTTP ");
      Serial.println(code);

      if (code > 0) {
        String resp = http.getString();
        Serial.println("Response:");
        Serial.println(resp);
      }
      http.end();
    } else {
      Serial.println("WiFi not connected");
    }
  }

  delay(5); // ~200Hz sampling
}
