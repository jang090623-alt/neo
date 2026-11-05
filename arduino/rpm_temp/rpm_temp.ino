// 유성기어 시험기 측정 전용 (Arduino UNO, USB 전원)
// - 홀센서 DO 2개: 입력축 D2, 출력축 D3 (자석 1개 = 한 바퀴 1펄스)
// - DS18B20: D4 (D4-5V 사이 4.7kΩ)
// - 모터는 외부 전원으로 따로 구동 (이 코드는 모터를 제어하지 않음)
// 시리얼 모니터 115200, 1초마다 쉼표 구분 출력 -> 그대로 엑셀에 붙여 넣기 가능
// 필요한 라이브러리: OneWire, DallasTemperature

#include <OneWire.h>
#include <DallasTemperature.h>

const int PIN_IN   = 2;   // 입력축(sun) 홀센서 DO  (UNO 인터럽트 핀: 2, 3)
const int PIN_OUT  = 3;   // 출력축(carrier) 홀센서 DO
const int PIN_TEMP = 4;   // DS18B20 DATA

// 신호가 0이거나 2배로 세지면 FALLING <-> RISING 바꿔 보기
#define HALL_EDGE FALLING

// 잡음 무시 간격: 이보다 짧은 펄스는 버림. 입력 최대 188 RPM = 319 ms/회전 이므로 50 ms면 충분히 안전 (최대 1200 RPM)
const unsigned long MIN_GAP_US = 50000UL;
// 이 시간 동안 펄스가 없으면 0 RPM 으로 표시 (출력축은 약 47 RPM = 1.28 s/회전 이라 더 길게)
const unsigned long TIMEOUT_IN_US  = 2000000UL;
const unsigned long TIMEOUT_OUT_US = 5000000UL;

OneWire oneWire(PIN_TEMP);
DallasTemperature sensors(&oneWire);

struct Axis { volatile unsigned long last, period, count; };
Axis inAx = {0, 0, 0}, outAx = {0, 0, 0};

void pulse(Axis &a) {
  unsigned long now = micros();
  if (a.count > 0 && now - a.last < MIN_GAP_US) return;   // 잡음(채터링) 무시
  if (a.count > 0) a.period = now - a.last;               // 첫 펄스는 간격 없음
  a.last = now;
  a.count++;
}
void isrIn()  { pulse(inAx); }
void isrOut() { pulse(outAx); }

// 인터럽트 중 값이 바뀌지 않게 한 번에 복사
void snapshot(Axis &a, unsigned long &last, unsigned long &period, unsigned long &count) {
  noInterrupts(); last = a.last; period = a.period; count = a.count; interrupts();
}

float rpmOf(unsigned long last, unsigned long period, unsigned long timeout) {
  if (period == 0 || micros() - last > timeout) return 0;
  return 60000000.0 / period;
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_IN, INPUT_PULLUP);
  pinMode(PIN_OUT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_IN), isrIn, HALL_EDGE);
  attachInterrupt(digitalPinToInterrupt(PIN_OUT), isrOut, HALL_EDGE);

  sensors.begin();
  if (sensors.getDeviceCount() == 0) Serial.println("# 경고: DS18B20 을 찾지 못함 (배선/4.7k 저항 확인)");
  sensors.setResolution(12);
  sensors.setWaitForConversion(false);   // 변환(최대 750 ms) 기다리지 않음
  sensors.requestTemperatures();

  Serial.println("time_s,input_rpm,output_rpm,input_rev,output_rev,rpm_diff,ratio,oil_temp_C");
}

unsigned long lastPrint = 0;

void loop() {
  if (millis() - lastPrint < 1000) return;
  lastPrint += 1000;

  float t = sensors.getTempCByIndex(0);   // 1초 전에 요청한 값
  sensors.requestTemperatures();

  unsigned long li, pi, ci, lo, po, co;
  snapshot(inAx, li, pi, ci);
  snapshot(outAx, lo, po, co);
  float inR  = rpmOf(li, pi, TIMEOUT_IN_US);
  float outR = rpmOf(lo, po, TIMEOUT_OUT_US);

  Serial.print(millis() / 1000.0, 1); Serial.print(',');
  Serial.print(inR, 1);  Serial.print(',');
  Serial.print(outR, 1); Serial.print(',');
  Serial.print(ci);      Serial.print(',');
  Serial.print(co);      Serial.print(',');
  Serial.print(inR - outR, 1); Serial.print(',');
  if (outR > 0) Serial.print(inR / outR, 2); else Serial.print('-');
  Serial.print(',');
  if (t == DEVICE_DISCONNECTED_C) Serial.println("ERR"); else Serial.println(t, 2);
}
