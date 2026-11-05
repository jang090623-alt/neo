// 윤활유 비교 실험 - 유성기어 시험기 (Arduino UNO + TB6612FNG + 홀센서 2개 + DS18B20)
// 켜면 3초 뒤 모터가 천천히 출발 -> PWM_SET 으로 고정 -> RUN_MIN 분 뒤 자동 정지
// 시리얼 모니터(115200)에 1초마다 쉼표로 구분해 출력 -> 복사해서 엑셀에 붙여 넣기
// 시리얼 모니터에서 x 를 보내면 바로 정지
// 필요한 라이브러리: OneWire, DallasTemperature (라이브러리 매니저에서 설치)

#include <OneWire.h>
#include <DallasTemperature.h>

// ===== 실험 조건 (오일마다 똑같이) =====
const int   PWM_SET   = 200;    // 모터 세기 0~255
const int   RUN_MIN   = 30;     // 실험 시간 [분]
const float TEMP_STOP = 50.0;   // 이 온도[°C] 넘으면 정지 (PLA 보호)

// ===== 핀 (실제 배선에 맞게 수정) =====
const int PIN_PWMA = 5;   // TB6612 PWMA (PWM 핀이어야 함: 3,5,6,9,10,11)
const int PIN_AIN1 = 7;   // TB6612 AIN1
const int PIN_AIN2 = 8;   // TB6612 AIN2
const int PIN_STBY = 9;   // TB6612 STBY
const int PIN_HALL_IN  = 2;   // 입력축(sun, 짧은 막대) 홀센서 DO  ※ UNO 는 2,3번만 인터럽트 가능
const int PIN_HALL_OUT = 3;   // 출력축(긴 막대) 홀센서 DO
const int PIN_TEMP = 4;       // DS18B20 데이터선 (5V 와 사이에 4.7kΩ)

// 홀센서 신호가 0 이거나 2배로 나오면 FALLING 을 RISING 으로 바꿔 보기
#define HALL_EDGE FALLING

const unsigned long MIN_GAP_US  = 20000UL;    // 20 ms 보다 짧은 신호는 잡음으로 무시 (최대 3000 RPM)
const unsigned long TIMEOUT_US  = 5000000UL;  // 5 초 동안 신호 없으면 0 RPM

OneWire oneWire(PIN_TEMP);
DallasTemperature temp(&oneWire);

// 펄스 사이 시간으로 회전수 계산 (자석 1개 = 한 바퀴에 펄스 1번)
volatile unsigned long lastIn = 0, periodIn = 0, lastOut = 0, periodOut = 0;

void isrIn() {
  unsigned long now = micros();
  if (now - lastIn > MIN_GAP_US) { periodIn = now - lastIn; lastIn = now; }
}
void isrOut() {
  unsigned long now = micros();
  if (now - lastOut > MIN_GAP_US) { periodOut = now - lastOut; lastOut = now; }
}

float rpmOf(volatile unsigned long &last, volatile unsigned long &period) {
  noInterrupts(); unsigned long l = last, p = period; interrupts();
  if (p == 0 || micros() - l > TIMEOUT_US) return 0;
  return 60000000.0 / p;
}

void motor(int pwm) { analogWrite(PIN_PWMA, pwm); }

bool running = true;
unsigned long startMs;

void stopAll(const char *why) {
  motor(0);
  digitalWrite(PIN_STBY, LOW);
  running = false;
  Serial.print("# 정지: "); Serial.println(why);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_PWMA, OUTPUT); pinMode(PIN_AIN1, OUTPUT); pinMode(PIN_AIN2, OUTPUT); pinMode(PIN_STBY, OUTPUT);
  motor(0);
  digitalWrite(PIN_AIN1, HIGH); digitalWrite(PIN_AIN2, LOW);   // 회전 방향 (반대로 돌면 두 값을 바꾸기)
  digitalWrite(PIN_STBY, HIGH);

  pinMode(PIN_HALL_IN, INPUT_PULLUP); pinMode(PIN_HALL_OUT, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(PIN_HALL_IN), isrIn, HALL_EDGE);
  attachInterrupt(digitalPinToInterrupt(PIN_HALL_OUT), isrOut, HALL_EDGE);

  temp.begin();
  temp.setWaitForConversion(false);   // 온도 읽는 동안 멈추지 않게
  temp.requestTemperatures();

  Serial.print("# PWM="); Serial.print(PWM_SET);
  Serial.print(", 시간="); Serial.print(RUN_MIN); Serial.println("분, 3초 뒤 시작");
  Serial.println("time_s,pwm,input_rpm,output_rpm,ratio,oil_temp_C");
  delay(3000);

  // 천천히 출발 (약 5초)
  for (int p = 0; p <= PWM_SET; p += 5) { motor(p); delay(5000L * 5 / PWM_SET); }
  motor(PWM_SET);
  startMs = millis();
}

unsigned long lastPrint = 0;

void loop() {
  if (Serial.available() && Serial.read() == 'x' && running) stopAll("x 입력");
  if (millis() - lastPrint < 1000) return;
  lastPrint = millis();

  float t = temp.getTempCByIndex(0);   // 1초 전에 요청한 값
  temp.requestTemperatures();          // 다음 1초용 요청

  float inR = rpmOf(lastIn, periodIn), outR = rpmOf(lastOut, periodOut);
  float sec = (millis() - startMs) / 1000.0;

  Serial.print(sec, 0); Serial.print(',');
  Serial.print(running ? PWM_SET : 0); Serial.print(',');
  Serial.print(inR, 1); Serial.print(',');
  Serial.print(outR, 1); Serial.print(',');
  if (outR > 0) Serial.print(inR / outR, 2); else Serial.print("-");
  Serial.print(',');
  if (t == DEVICE_DISCONNECTED_C) Serial.println("ERR"); else Serial.println(t, 2);

  if (!running) return;
  if (t != DEVICE_DISCONNECTED_C && t > TEMP_STOP) stopAll("온도 초과");
  else if (sec >= RUN_MIN * 60.0) stopAll("시간 종료");
}
