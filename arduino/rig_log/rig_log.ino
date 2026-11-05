// 시험 3 유성기어 시험기 계측 (Arduino UNO, USB 전원) - 친구 코드(홀센서·DS18B20)에 발전기 전압을 더한 것
// 홀센서 DO: 입력축(sun, 짧은 막대) D2 / 출력축(긴 막대) D3,  DS18B20: D4 (4.7kΩ 풀업, 2개면 0=오일, 1=실내)
// 발전기(모터 2): 두 선을 부하 저항 R 양 끝에 연결. 저항 + 쪽 -> 1kΩ -> A0, 저항 - 쪽 -> GND
// 모터 1 전류는 전원 공급기 화면에서 읽어 기록지에 적는다 (전류 센서 없음)
// 출력: 1초마다 CSV 한 줄 (시리얼 모니터 9600 -> 복사해서 저장)

#include <OneWire.h>
#include <DallasTemperature.h>

const float R_LOAD = 22.0;      // 부하 저항 [Ω] - 실제 저항값으로 고치기 (멀티미터로 잰 값)
const int hallInputPin = 2, hallOutputPin = 3, tempPin = 4, genPin = A0;

OneWire oneWire(tempPin);
DallasTemperature sensors(&oneWire);

volatile unsigned long inputTotal = 0, outputTotal = 0;
volatile unsigned long inputLastPulse = 0, outputLastPulse = 0;
volatile unsigned long inputPeriod = 0, outputPeriod = 0;

const unsigned long minPulseGap = 50000UL;    // 50 ms 보다 짧은 신호는 잡음 (입력 최대 188 RPM = 319 ms/회전)
const unsigned long stopTimeout = 3000000UL;  // 3 s 동안 신호 없으면 0 RPM

float oilTemp = DEVICE_DISCONNECTED_C, roomTemp = DEVICE_DISCONNECTED_C;
bool tempPending = false;
unsigned long tempRequestTime = 0, lastTempRequest = 0, lastPrintTime = 0;

void pulse(volatile unsigned long &last, volatile unsigned long &period, volatile unsigned long &total) {
  unsigned long now = micros();
  if (last == 0 || now - last >= minPulseGap) {
    if (last != 0) period = now - last;
    last = now;
    total++;
  }
}
void inputHallISR()  { pulse(inputLastPulse, inputPeriod, inputTotal); }
void outputHallISR() { pulse(outputLastPulse, outputPeriod, outputTotal); }

float rpmOf(unsigned long period, unsigned long last, unsigned long nowUs) {
  if (last == 0 || period == 0 || nowUs - last > stopTimeout) return 0;
  return 60000000.0 / period;
}

void printTemp(float t) {
  if (t == DEVICE_DISCONNECTED_C || isnan(t)) Serial.print("ERR"); else Serial.print(t, 2);
}

void setup() {
  Serial.begin(9600);
  pinMode(hallInputPin, INPUT_PULLUP);
  pinMode(hallOutputPin, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(hallInputPin), inputHallISR, FALLING);
  attachInterrupt(digitalPinToInterrupt(hallOutputPin), outputHallISR, FALLING);

  sensors.begin();
  sensors.setResolution(10);
  sensors.setWaitForConversion(false);
  sensors.requestTemperatures();
  tempPending = true;
  tempRequestTime = lastTempRequest = lastPrintTime = millis();

  Serial.print("# R_LOAD="); Serial.print(R_LOAD); Serial.print(" ohm, DS18B20 개수="); Serial.println(sensors.getDeviceCount());
  Serial.println("time_s,input_rpm,output_rpm,ratio,input_turns,output_turns,gen_V,gen_P_W,oil_C,room_C");
}

void loop() {
  unsigned long nowMs = millis();

  if (tempPending && nowMs - tempRequestTime >= 200) {      // 10비트 변환 약 188 ms
    oilTemp = sensors.getTempCByIndex(0);
    roomTemp = sensors.getTempCByIndex(1);
    tempPending = false;
  }
  if (!tempPending && nowMs - lastTempRequest >= 1000) {
    sensors.requestTemperatures();
    tempRequestTime = lastTempRequest = nowMs;
    tempPending = true;
  }

  if (nowMs - lastPrintTime < 1000) return;
  lastPrintTime = nowMs;

  unsigned long inT, outT, inL, outL, inP, outP;
  noInterrupts();
  inT = inputTotal; outT = outputTotal; inL = inputLastPulse; outL = outputLastPulse; inP = inputPeriod; outP = outputPeriod;
  interrupts();
  unsigned long nowUs = micros();
  float inR = rpmOf(inP, inL, nowUs), outR = rpmOf(outP, outL, nowUs);

  long raw = 0;
  for (int i = 0; i < 16; i++) raw += analogRead(genPin);    // 16번 평균 (모터 잡음 줄이기)
  float genV = raw / 16.0 * 5.0 / 1023.0;                    // UNO 5V 기준 (USB 전압이 4.8~5.1 V 라 ±4% 오차)
  float genP = genV * genV / R_LOAD;                          // 출력 전력 P_out = V^2 / R

  Serial.print(nowMs / 1000.0, 1); Serial.print(',');
  Serial.print(inR, 1); Serial.print(',');
  Serial.print(outR, 1); Serial.print(',');
  if (outR > 0) Serial.print(inR / outR, 2); else Serial.print('-');
  Serial.print(',');
  Serial.print(inT); Serial.print(',');
  Serial.print(outT); Serial.print(',');
  Serial.print(genV, 3); Serial.print(',');
  Serial.print(genP, 4); Serial.print(',');
  printTemp(oilTemp); Serial.print(',');
  printTemp(roomTemp);
  Serial.println();
}
