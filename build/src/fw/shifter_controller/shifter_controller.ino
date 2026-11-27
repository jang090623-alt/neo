// 3D프린팅 수동변속기 → PC 게임 컨트롤러 + 모터 보호 (아두이노 레오나르도 / Pro Micro)  v4
// 필요한 라이브러리: "Joystick" by Matthew Heironimus (ArduinoJoystickLibrary)
//
// v4에서 바뀐 점
//  1) 출력축 rpm: 펄스 사이 시간으로 계산 (v4.1: 자석 4개)
//  2) 모터 허가 출력(RELAY_PIN): 5V 릴레이 모듈 → 주 릴레이(40A) 코일 회로에 직렬 (비상정지·덮개 스위치와 함께)
//     - 켤 때: 가속 페달을 뗀 상태(5% 미만)가 0.5초 이어져야 허가 → 페달 밟은 채 켜져도 모터가 갑자기 돌지 않음
//     - 막힘 감시: 기어가 들어가 있고 + 클러치를 뗐고 + 가속 30% 이상인데 출력축 자석 펄스가 5초 동안 없으면 → 모터 차단
//       (출력이 막히면 클러치가 계속 미끄러져 열이 남: 계산서 3-2, 5초면 와셔 +3.5K, 60초면 +42K)
//     - 다시 허가: 가속 페달을 1초 동안 떼면
//  3) v4.1 안전 회로 감지(SAFETY_PIN): 비상정지·덮개 스위치 뒤 12V 를 10k/4.7k 로 나눠 읽음 (닫힘 = HIGH)
//     → 비상정지를 누르거나 덮개를 열면 WAIT 로 돌아감 → 풀어도 가속 페달을 뗄 때까지 모터가 다시 돌지 않음
//  게임과의 약속(축·버튼)은 v3와 같습니다.
//   축0(X)=핸들 축1(Y)=가속 축2(Z)=클러치 축3(Rx)=출력축 rpm(0~2000) 축4(Ry)=브레이크
//   버튼0~4=1~5단 버튼5=후진 (아무 버튼도 안 눌림=중립) 버튼6=코스 복귀

#include <Joystick.h>

// ---------- 핀 ----------
const byte GEAR_PIN[6] = {4, 5, 6, 8, 9, 10};  // 1단, 2단, 3단, 4단, 5단, 후진 (A3144: 자석 가까이 → LOW)
const byte RESET_PIN   = 11;                   // 코스 복귀 버튼 (누르면 LOW)
const byte RPM_PIN     = 7;                    // 출력축 홀 센서 (인터럽트 핀)
const byte RELAY_PIN   = 12;                   // 5V 릴레이 모듈 IN (모터 허가)
const byte SAFETY_PIN  = A4;                   // 안전 회로 감지 (12V → 10k → 핀 → 4.7k → GND)
const byte PEDAL_PIN   = A0;                   // 가속 페달 신호 (0~5V 확인 후 연결)
const byte CLUTCH_PIN  = A1;                   // 클러치 페달 가변저항
const byte STEER_PIN   = A2;                   // 핸들 가변저항
const byte BRAKE_PIN   = A3;                   // 브레이크 페달 가변저항

// ---------- 보정값 (시리얼 모니터 115200 의 raw 값을 보고 바꾸세요) ----------
int PEDAL_MIN = 0,   PEDAL_MAX = 1023;
int CLUTCH_MIN = 0,  CLUTCH_MAX = 1023;        // 클러치 뗐을 때 = MIN, 끝까지 밟았을 때 = MAX
int STEER_MIN = 0,   STEER_MAX = 1023;
int BRAKE_MIN = 0,   BRAKE_MAX = 1023;
const byte MAGNETS_PER_TURN = 4;               // v4.1: 표시 바퀴 자석 4개
const int  RPM_MAX = 2000;
const bool RELAY_ACTIVE_LOW = true;            // 흔한 릴레이 모듈은 IN=LOW 일 때 켜짐. 반대면 false

// ---------- 모터 보호 기준 (0~1023 으로 편 값) ----------
const int  PEDAL_IDLE = 51;                    // 5%
const int  PEDAL_PUSH = 307;                   // 30%
const int  CLUTCH_FREE = 153;                  // 15% 미만 = 클러치 뗌
const unsigned long JAM_MS = 5000, ARM_MS = 500, REARM_MS = 1000;   // 막힘 5초 = 와셔 +3.5K (계산서 3-2)

Joystick_ Joystick(JOYSTICK_DEFAULT_REPORT_ID, JOYSTICK_TYPE_JOYSTICK,
                   7, 0, true, true, true, true, true, false, false, false, false, false);

volatile unsigned long lastPulseUs = 0, periodUs = 0;
void onPulse() {
  unsigned long t = micros();
  if (t - lastPulseUs > 3000) { periodUs = t - lastPulseUs; lastPulseUs = t; }   // 3ms 미만 잡음 무시
}

int scaled(int raw, int lo, int hi) { return constrain(map(raw, lo, hi, 0, 1023), 0, 1023); }

void setRelay(bool on) { digitalWrite(RELAY_PIN, (on ^ RELAY_ACTIVE_LOW) ? HIGH : LOW); }

void setup() {
  setRelay(false); pinMode(RELAY_PIN, OUTPUT);           // 출력으로 바꾸기 전에 차단 값을 먼저 써서 켜지는 순간의 짧은 ON 을 막음
  for (byte i = 0; i < 6; i++) pinMode(GEAR_PIN[i], INPUT_PULLUP);
  pinMode(RPM_PIN, INPUT_PULLUP);
  pinMode(RESET_PIN, INPUT_PULLUP);
  pinMode(SAFETY_PIN, INPUT);
  attachInterrupt(digitalPinToInterrupt(RPM_PIN), onPulse, FALLING);
  Joystick.setXAxisRange(0, 1023); Joystick.setYAxisRange(0, 1023); Joystick.setZAxisRange(0, 1023);
  Joystick.setRxAxisRange(0, RPM_MAX); Joystick.setRyAxisRange(0, 1023);
  Joystick.begin();
  Serial.begin(115200);
}

enum State { WAIT_IDLE, ARMED, TRIPPED };
State st = WAIT_IDLE;
unsigned long idleSince = 0, jamSince = 0, lastPrint = 0;

void loop() {
  unsigned long now = millis();
  // 1) 기어
  byte on = 0, gear = 0;
  for (byte i = 0; i < 6; i++) if (digitalRead(GEAR_PIN[i]) == LOW) { on++; gear = i + 1; }
  for (byte i = 0; i < 6; i++) Joystick.setButton(i, on == 1 && gear == i + 1);
  Joystick.setButton(6, digitalRead(RESET_PIN) == LOW);
  // 2) 아날로그
  int pedalRaw = analogRead(PEDAL_PIN), clutchRaw = analogRead(CLUTCH_PIN), steerRaw = analogRead(STEER_PIN), brakeRaw = analogRead(BRAKE_PIN);
  int pedal = scaled(pedalRaw, PEDAL_MIN, PEDAL_MAX), clutch = scaled(clutchRaw, CLUTCH_MIN, CLUTCH_MAX);
  Joystick.setXAxis(scaled(steerRaw, STEER_MIN, STEER_MAX));
  Joystick.setYAxis(pedal);
  Joystick.setZAxis(clutch);
  Joystick.setRyAxis(scaled(brakeRaw, BRAKE_MIN, BRAKE_MAX));
  // 3) rpm: 마지막 펄스 간격, 2초 동안 펄스가 없으면 0
  noInterrupts(); unsigned long last = lastPulseUs, per = periodUs; interrupts();
  int rpm = 0;
  if (per > 0 && micros() - last < 2000000UL) rpm = (long)(60000000UL / per) / MAGNETS_PER_TURN;
  Joystick.setRxAxis(min(rpm, RPM_MAX));
  // 4) 모터 허가
  bool idle = pedal < PEDAL_IDLE;
  if (idle) { if (idleSince == 0) idleSince = now; } else idleSince = 0;
  bool safetyOk = digitalRead(SAFETY_PIN) == HIGH;
  if (!safetyOk) { st = WAIT_IDLE; idleSince = 0; jamSince = 0; }   // 비상정지·덮개 열림: 다시 허가하려면 페달을 뗀 상태가 이어져야 함
  if (st == WAIT_IDLE && idleSince && now - idleSince >= ARM_MS) st = ARMED;
  bool turning = (micros() - last) < JAM_MS * 1000UL;       // 막힘 판단은 rpm 이 아니라 '마지막 펄스 이후 시간' (느린 1단·약한 페달에서 오작동 방지)
  bool jamCond = (on == 1) && (clutch < CLUTCH_FREE) && (pedal > PEDAL_PUSH) && !turning;
  if (st == ARMED) {
    if (jamCond) { if (jamSince == 0) jamSince = now; if (now - jamSince >= JAM_MS) st = TRIPPED; }
    else jamSince = 0;
  }
  if (st == TRIPPED && idleSince && now - idleSince >= REARM_MS) { st = ARMED; jamSince = 0; }
  setRelay(st == ARMED);
  // 5) 보정·상태 출력
  if (now - lastPrint >= 200) {
    lastPrint = now;
    Serial.print("pedal="); Serial.print(pedalRaw);
    Serial.print(" clutch="); Serial.print(clutchRaw);
    Serial.print(" steer="); Serial.print(steerRaw);
    Serial.print(" brake="); Serial.print(brakeRaw);
    Serial.print(" gearSensors="); Serial.print(on);
    Serial.print(" rpm="); Serial.print(rpm);
    Serial.print(" safety="); Serial.print(safetyOk ? "OK" : "OPEN");
    Serial.print(" motor="); Serial.println(st == ARMED ? "ON" : (st == TRIPPED ? "TRIP(페달을 1초 떼세요)" : "WAIT(페달을 떼세요)"));
  }
  delay(5);
}
