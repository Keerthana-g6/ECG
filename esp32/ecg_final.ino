#include <WiFi.h>
#include <HTTPClient.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// Pins
#define ECG_PIN 34
#define BUZZER_PIN 27

// WiFi
const char* ssid     = "YOUR_WIFI";
const char* password = "YOUR_PASSWORD";

// Backend URL
String serverUrlInfer = "http://YOUR_LAPTOP_IP:5000/infer";
String serverUrlResult = "http://YOUR_LAPTOP_IP:5000/latest_result";

const int N_SAMPLES = 1000;
int ecgBuf[N_SAMPLES];
int idx = 0;

void setup() {
  Serial.begin(115200);

  // OLED
  Wire.begin(21, 22);   // SDA=21, SCL=22
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);
  display.println("ECG System Booting...");
  display.display();

  // Buzzer
  pinMode(BUZZER_PIN, OUTPUT);

  // WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Connecting WiFi...");
    display.display();
    delay(500);
  }

  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("WiFi Connected!");
  display.display();
  delay(1000);
}

void loop() {
  int raw = analogRead(ECG_PIN);
  ecgBuf[idx++] = raw;

  if (idx >= N_SAMPLES) {  
    idx = 0;

    // SEND ECG to backend
    HTTPClient http;
    http.begin(serverUrlInfer);
    http.addHeader("Content-Type", "application/json");

    String payload = "{\"ecg\":[";
    for (int i = 0; i < N_SAMPLES; i++) {
      payload += ecgBuf[i];
      if (i < N_SAMPLES - 1) payload += ",";
    }
    payload += "]}";

    int code = http.POST(payload);
    http.end();
  }

  // FETCH ML RESULT
  HTTPClient http2;
  http2.begin(serverUrlResult);
  int code2 = http2.GET();

  if (code2 == 200) {
    String body = http2.getString();
    Serial.println(body);

    // Parse minimal JSON manually
    String disease = getValue(body, "disease");
    String riskStr = getValue(body, "risk");
    float risk = riskStr.toFloat();

    // Show on OLED
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("Disease:");
    display.println(disease);
    display.println("");
    display.print("Risk: ");
    display.print(risk);
    display.println("%");
    display.display();

    // BUZZER alarm
    if (risk > 60) {
      tone(BUZZER_PIN, 1000);  // beep
    } else {
      noTone(BUZZER_PIN);
    }
  }
  http2.end();

  delay(500);  
}

// Helper to extract JSON field
String getValue(String json, String key) {
  int s = json.indexOf(key) + key.length() + 3;
  int e = json.indexOf("\"", s);
  return json.substring(s, e);
}
