/*
 * ESP32-CAM firmware
 *
 *   Port 81  GET /stream   MJPEG video (VGA 640x480)
 *   Port 80  GET /control?dir=F|B|L|R|S&speed=0-255   drive command
 *   Port 80  GET /status   Wi-Fi signal strength, uptime, free heap (JSON)
 *   Port 80  GET /capture  single JPEG frame
 *
 * Drive commands are forwarded to the Arduino Uno over UART1 as "<dir>,<speed>\n".
 * The Uno owns the motors and stops them on its own if commands stop arriving.
 *
 * Board:  AI Thinker ESP32-CAM  (ESP32 Arduino core 2.x or 3.x)
 */
#include <WiFi.h>
#include "esp_camera.h"
#include "esp_http_server.h"
#include "camera_pins.h"
#include "secrets.h"

// UART1 link to the Arduino Uno. Only TX is used: GPIO14 -> Uno D2.
// Keeping UART0 free means USB flashing and Serial debug still work.
static const int UNO_TX_PIN = 14;
static const int UNO_RX_PIN = 13;  // unused, UART1 just needs a valid pin
static const long UNO_BAUD = 9600;

static httpd_handle_t control_httpd = NULL;
static httpd_handle_t stream_httpd = NULL;

static void unoSend(char dir, int speed) {
  Serial1.printf("%c,%d\n", dir, speed);
}

static bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = FRAMESIZE_VGA;  // 640x480
  config.jpeg_quality = 12;           // 10 = best quality, 63 = smallest
  config.fb_count = psramFound() ? 2 : 1;
  config.fb_location = psramFound() ? CAMERA_FB_IN_PSRAM : CAMERA_FB_IN_DRAM;
  config.grab_mode = CAMERA_GRAB_LATEST;  // always serve the newest frame

  return esp_camera_init(&config) == ESP_OK;
}

static esp_err_t stream_handler(httpd_req_t *req) {
  esp_err_t res = httpd_resp_set_type(req, "multipart/x-mixed-replace;boundary=frame");
  if (res != ESP_OK) return res;
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

  char part[64];
  while (true) {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      res = ESP_FAIL;
    } else {
      size_t n = snprintf(part, sizeof(part),
                          "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n",
                          (unsigned)fb->len);
      res = httpd_resp_send_chunk(req, "--frame\r\n", 9);
      if (res == ESP_OK) res = httpd_resp_send_chunk(req, part, n);
      if (res == ESP_OK) res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
      if (res == ESP_OK) res = httpd_resp_send_chunk(req, "\r\n", 2);
      esp_camera_fb_return(fb);
    }
    if (res != ESP_OK) break;  // client disconnected
  }
  return res;
}

static esp_err_t capture_handler(httpd_req_t *req) {
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    httpd_resp_send_500(req);
    return ESP_FAIL;
  }
  httpd_resp_set_type(req, "image/jpeg");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  esp_err_t res = httpd_resp_send(req, (const char *)fb->buf, fb->len);
  esp_camera_fb_return(fb);
  return res;
}

static esp_err_t control_handler(httpd_req_t *req) {
  char query[64];
  char dir[4] = {0};
  char spd[8] = {0};

  if (httpd_req_get_url_query_str(req, query, sizeof(query)) != ESP_OK ||
      httpd_query_key_value(query, "dir", dir, sizeof(dir)) != ESP_OK) {
    httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "dir is required (F, B, L, R or S)");
    return ESP_FAIL;
  }

  char c = toupper(dir[0]);
  if (c == 0 || strchr("FBLRS", c) == NULL) {
    httpd_resp_send_err(req, HTTPD_400_BAD_REQUEST, "dir must be F, B, L, R or S");
    return ESP_FAIL;
  }

  int speed = 200;
  if (httpd_query_key_value(query, "speed", spd, sizeof(spd)) == ESP_OK) {
    speed = constrain(atoi(spd), 0, 255);
  }

  unoSend(c, c == 'S' ? 0 : speed);
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, "ok", 2);
}

static esp_err_t status_handler(httpd_req_t *req) {
  char json[128];
  snprintf(json, sizeof(json), "{\"rssi\":%d,\"uptime_s\":%lu,\"free_heap\":%u}",
           WiFi.RSSI(), (unsigned long)(millis() / 1000), (unsigned)ESP.getFreeHeap());
  httpd_resp_set_type(req, "application/json");
  httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
  return httpd_resp_send(req, json, strlen(json));
}

static void startServers() {
  httpd_uri_t control_uri = {"/control", HTTP_GET, control_handler, NULL};
  httpd_uri_t status_uri = {"/status", HTTP_GET, status_handler, NULL};
  httpd_uri_t capture_uri = {"/capture", HTTP_GET, capture_handler, NULL};
  httpd_uri_t stream_uri = {"/stream", HTTP_GET, stream_handler, NULL};

  // Two servers: the stream handler blocks its server, so control must live elsewhere.
  httpd_config_t config = HTTPD_DEFAULT_CONFIG();
  config.server_port = 80;
  if (httpd_start(&control_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(control_httpd, &control_uri);
    httpd_register_uri_handler(control_httpd, &status_uri);
    httpd_register_uri_handler(control_httpd, &capture_uri);
  }

  config.server_port = 81;
  config.ctrl_port += 1;
  if (httpd_start(&stream_httpd, &config) == ESP_OK) {
    httpd_register_uri_handler(stream_httpd, &stream_uri);
  }
}

void setup() {
  Serial.begin(115200);
  Serial1.begin(UNO_BAUD, SERIAL_8N1, UNO_RX_PIN, UNO_TX_PIN);
  unoSend('S', 0);

  if (!initCamera()) {
    Serial.println("Camera init failed, restarting");
    delay(3000);
    ESP.restart();
  }

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  WiFi.setSleep(false);  // Wi-Fi power saving adds tens of ms of latency

  unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(300);
    Serial.print(".");
    if (millis() - start > 20000) {
      Serial.println("\nWi-Fi connect timed out, restarting");
      ESP.restart();
    }
  }
  Serial.printf("\nConnected. Open http://%s:81/stream\n", WiFi.localIP().toString().c_str());

  startServers();
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    unoSend('S', 0);  // never keep driving without a link
    WiFi.reconnect();
    delay(2000);
  }
  delay(500);
}
