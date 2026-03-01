/*
  ESP32 ECG streamer + DAC output (configurable)
  - Streams ADC values over a WebSocket (port 81)
  - Outputs the filtered/reconstructed ECG analog signal either via:
      a) built-in ESP32 DAC (GPIO25)  [8-bit]
      b) external MCP4725 I2C DAC     [12-bit]

  Configure which DAC to use by changing USE_MCP4725 flag.

  Wiring (ADC input):
    AD8232 OUTPUT  -> ESP32 GPIO34 (ADC1 channel)
    AD8232 GND     -> ESP32 GND
    AD8232 3.3V    -> ESP32 3.3V

  Built-in DAC wiring (simple):
    ESP32 GPIO25 (DAC1) -> Oscilloscope input (with common ground)

  MCP4725 wiring (external DAC - recommended for higher fidelity):
    MCP4725 VCC -> ESP32 3.3V
    MCP4725 GND -> ESP32 GND
    MCP4725 SDA -> ESP32 GPIO21 (SDA)
    MCP4725 SCL -> ESP32 GPIO22 (SCL)

  Notes: keep the ESP32 and oscilloscope/common ground connected. Use a power bank for safety during live demos.
*/

#include <WiFi.h>
#include <WebSocketsServer.h>
#include <Wire.h>

// Uncomment to use external MCP4725 DAC (Adafruit_MCP4725 library required)
#define USE_MCP4725 1

#if USE_MCP4725
  #include <Adafruit_MCP4725.h>
#endif

// ECG ADC pin
#define ECG_PIN 34  // ADC1_CH6

// ESP32 built-in DAC pin (GPIO25) - 8-bit (0..255)
#define ESP32_DAC_PIN 25

// WiFi AP credentials (softAP mode)
const char* ssid = "ECG_WIFI";
const char* password = "12345678";

WebSocketsServer webSocket = WebSocketsServer(81);

#if USE_MCP4725
Adafruit_MCP4725 dac;
#endif

// Simple single-pole filter state
float hp_prev_x = 0.0;
float hp_prev_y = 0.0;
float lp_prev_y = 0.0;

// Map ADC raw to DAC range helper
inline uint16_t mapTo12bit(int v){
  // ESP32 ADC returns 0..4095 (12-bit) on default; constrain then return
  int val = v;
  if(val < 0) val = 0;
  if(val > 4095) val = 4095;
  return (uint16_t)val; // 0..4095 for 12-bit DAC
}

inline uint8_t mapTo8bit(int v){
  int val = v;
  if(val < 0) val = 0;
  if(val > 4095) val = 4095;
  return (uint8_t)(val >> 4); // map 0..4095 to 0..255
}

// Very small digital filter: high-pass + low-pass (cheap approximation)
int filterECG_sample(int raw){
  float x = (float)raw;
  // high-pass simple IIR: y[n] = 0.97*y[n-1] + x[n] - x[n-1]
  float hp = 0.97f * hp_prev_y + x - hp_prev_x;
  hp_prev_x = x;
  hp_prev_y = hp;

  // low-pass simple IIR: y[n] = y[n-1] + a*(hp - y[n-1])
  const float a = 0.1f; // smoothing factor
  float lp = lp_prev_y + a * (hp - lp_prev_y);
  lp_prev_y = lp;

  // Center and scale for DAC output
  int out = (int)lp;
  // shift baseline to positive (optional): add offset if needed
  return out;
}

void setup() {
  Serial.begin(115200);
  // Start WiFi AP so frontend or laptop can connect directly
  WiFi.softAP(ssid, password);
  Serial.println("WiFi Started: ECG_WIFI");

  webSocket.begin();
  Serial.println("WebSocket Started on port 81");

  // Init DAC (if using external)
  #if USE_MCP4725
    Wire.begin(21, 22); // SDA=21, SCL=22
    if(!dac.begin(0x60)){
      Serial.println("MCP4725 not found. Check wiring.");
    } else {
      Serial.println("MCP4725 DAC ready");
    }
  #else
    // No init required for built-in DAC
    pinMode(ESP32_DAC_PIN, OUTPUT);
  #endif

  // ADC config: attenuation to read up to Vref (optional)
  analogReadResolution(12); // 0..4095
  analogSetPinAttenuation(ECG_PIN, ADC_11db); // maximize input range
}

void loop() {
  webSocket.loop();

  int raw = analogRead(ECG_PIN); // 0..4095

  // Very small sanity check
  if(raw < 0) raw = 0;

  // Filtered sample
  int clean = filterECG_sample(raw);

  // Send raw (or send cleaned value) over WebSocket
  // Option: send cleaned value to make frontend waveform smoother
  webSocket.broadcastTXT(String(clean));

  // Output analog via selected DAC
  #if USE_MCP4725
    uint16_t v12 = mapTo12bit(clean);
    // MCP4725 expects 0..4095 for 12-bit
    dac.setVoltage(v12, false);
  #else
    uint8_t v8 = mapTo8bit(clean);
    dacWrite(ESP32_DAC_PIN, v8);
  #endif

  // ~200 Hz sampling -> 5000 microseconds
  delayMicroseconds(5000);
}