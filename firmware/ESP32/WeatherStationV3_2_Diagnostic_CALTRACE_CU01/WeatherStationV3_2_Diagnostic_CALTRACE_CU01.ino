/*
=========================================================
AtmosLink Research Platform
Firmware : WeatherStationV3_2_Diagnostic_CU01
Version  : 3.2-DIAG
Station  : CU01
Hardware : ESP32 + BME280 + Rain Gauge Direct GPIO

PURPOSE:
Diagnostic firmware for transient BME280 acquisition
anomalies at Cerro Cuñacales.

Normal AtmosLink 17-field CSV remains unchanged.

Diagnostic records:
INFO,DBG_BOOT,...
INFO,DBG_BME,...
INFO,DBG_MINUTE,...

DO NOT parse INFO lines as meteorological observations.
=========================================================
*/

#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME280.h>
#include <math.h>

#define STATION_ID "CU01"

#define SDA_PIN   21
#define SCL_PIN   22
#define RAIN_PIN  27

#define ATMOSLINK_BME280_ADDRESS 0x76

// Calibración experimental 2026-09-09: área 100 x 48 mm; 300 mL; 154, 151 y 148 cuentas
// Factor promedio obtenido: 0.4139 mm por basculación
const float MM_PER_TIP = 0.414;

const unsigned long SAMPLE_INTERVAL_MS = 60000;
const unsigned long READ_INTERVAL_MS   = 5000;
const unsigned long BME_WARMUP_MS      = 30000;

const unsigned long RAIN_POLL_MS       = 20;
const unsigned long RAIN_STABLE_MS     = 80;
const unsigned long RAIN_MIN_TIP_MS    = 2000;


class DiagnosticBME280 : public Adafruit_BME280
{
public:
  bme280_calib_data diagnosticCalibration() const
  {
    return _bme280_calib;
  }

  int32_t diagnosticTFine() const
  {
    return t_fine;
  }
};

DiagnosticBME280 bme;


unsigned long rainTipsTotal = 0;
unsigned long lastTipsTotal = 0;
float rainTotalMM = 0.0;

int rainRawLast = HIGH;
int rainStableState = HIGH;
int rainStableLast = HIGH;

unsigned long rainRawChangedAt = 0;
unsigned long lastRainPollTime = 0;
unsigned long lastAcceptedTipTime = 0;

unsigned long lastSampleTime = 0;
unsigned long lastReadTime = 0;

float tempSum = 0.0;
float humSum = 0.0;
float presSum = 0.0;

float tempMin = 999.0;
float tempMax = -999.0;

float humMin = 999.0;
float humMax = -999.0;

float pressureMin = 9999.0;
float pressureMax = -9999.0;

int sampleCount = 0;
int rejectedCount = 0;

float dewPoint(float temperature, float humidity)
{
  if (humidity <= 0.0)
    return NAN;

  const float a = 17.62;
  const float b = 243.12;

  float gamma =
      log(humidity / 100.0) +
      (a * temperature) / (b + temperature);

  return (b * gamma) / (a - gamma);
}

float vaporPressure(float temperature, float humidity)
{
  float saturation =
      6.112 *
      exp((17.67 * temperature) /
          (temperature + 243.5));

  return saturation * humidity / 100.0;
}

bool validBME(float t, float h, float p)
{
  if (!isfinite(t) ||
      !isfinite(h) ||
      !isfinite(p))
    return false;

  if (t < -30.0 || t > 60.0)
    return false;

  if (h < 0.0 || h > 100.0)
    return false;

  if (p < 500.0 || p > 1100.0)
    return false;

  return true;
}


// ATMOSLINK_PRESS_Y_RAW_ADC
// Lectura directa de los 8 bytes de datos BME280:
// 0xF7..0xF9 pressure, 0xFA..0xFC temperature,
// 0xFD..0xFE humidity.
// SOLO DIAGNOSTICO: no modifica los valores usados por AtmosLink.

// ============================================================
// ATMOSLINK PRESS-Y4B
// Independent coherent BME280 calibration/compensation
// Diagnostic only.
// Does NOT modify Adafruit_BME280 library.
// ============================================================

struct BMECalDiag {
  uint16_t T1;
  int16_t  T2;
  int16_t  T3;

  uint16_t P1;
  int16_t  P2;
  int16_t  P3;
  int16_t  P4;
  int16_t  P5;
  int16_t  P6;
  int16_t  P7;
  int16_t  P8;
  int16_t  P9;

  uint8_t  H1;
  int16_t  H2;
  uint8_t  H3;
  int16_t  H4;
  int16_t  H5;
  int8_t   H6;

  bool valid;
};

BMECalDiag diagCal = {};

bool diagReadRegs(uint8_t reg, uint8_t *buf, size_t len)
{
  const uint8_t BME_ADDR = 0x76;

  Wire.beginTransmission(BME_ADDR);
  Wire.write(reg);

  if (Wire.endTransmission(false) != 0)
    return false;

  size_t n = Wire.requestFrom(
      BME_ADDR,
      (uint8_t)len);

  if (n != len)
    return false;

  for (size_t i = 0; i < len; i++)
  {
    if (!Wire.available())
      return false;

    buf[i] = Wire.read();
  }

  return true;
}

uint16_t diagU16LE(const uint8_t *b)
{
  return (uint16_t)b[0] |
         ((uint16_t)b[1] << 8);
}

int16_t diagS16LE(const uint8_t *b)
{
  return (int16_t)diagU16LE(b);
}

bool loadDiagCalibration()
{
  uint8_t a[26];
  uint8_t h1;
  uint8_t h[7];

  if (!diagReadRegs(0x88, a, sizeof(a)))
    return false;

  if (!diagReadRegs(0xA1, &h1, 1))
    return false;

  if (!diagReadRegs(0xE1, h, sizeof(h)))
    return false;

  diagCal.T1 = diagU16LE(&a[0]);
  diagCal.T2 = diagS16LE(&a[2]);
  diagCal.T3 = diagS16LE(&a[4]);

  diagCal.P1 = diagU16LE(&a[6]);
  diagCal.P2 = diagS16LE(&a[8]);
  diagCal.P3 = diagS16LE(&a[10]);
  diagCal.P4 = diagS16LE(&a[12]);
  diagCal.P5 = diagS16LE(&a[14]);
  diagCal.P6 = diagS16LE(&a[16]);
  diagCal.P7 = diagS16LE(&a[18]);
  diagCal.P8 = diagS16LE(&a[20]);
  diagCal.P9 = diagS16LE(&a[22]);

  diagCal.H1 = h1;
  diagCal.H2 = diagS16LE(&h[0]);
  diagCal.H3 = h[2];

  diagCal.H4 =
      ((int16_t)(int8_t)h[3] << 4) |
      (h[4] & 0x0F);

  diagCal.H5 =
      ((int16_t)(int8_t)h[5] << 4) |
      (h[4] >> 4);

  diagCal.H6 = (int8_t)h[6];

  diagCal.valid = true;

  return true;
}


void printCalibrationTrace()
{
  bme280_calib_data a =
      bme.diagnosticCalibration();

  uint8_t regs[4] = {0, 0, 0, 0};

  bool cfgOk = true;

  cfgOk &= diagReadRegs(0xF2, &regs[0], 1);
  cfgOk &= diagReadRegs(0xF3, &regs[1], 1);
  cfgOk &= diagReadRegs(0xF4, &regs[2], 1);
  cfgOk &= diagReadRegs(0xF5, &regs[3], 1);

  Serial.print("INFO,DBG_CALTRACE,");
  Serial.print(millis());

  // Adafruit internal calibration
  Serial.print(",ADA,");
  Serial.print(a.dig_T1);
  Serial.print(",");
  Serial.print(a.dig_T2);
  Serial.print(",");
  Serial.print(a.dig_T3);

  Serial.print(",");
  Serial.print(a.dig_P1);
  Serial.print(",");
  Serial.print(a.dig_P2);
  Serial.print(",");
  Serial.print(a.dig_P3);
  Serial.print(",");
  Serial.print(a.dig_P4);
  Serial.print(",");
  Serial.print(a.dig_P5);
  Serial.print(",");
  Serial.print(a.dig_P6);
  Serial.print(",");
  Serial.print(a.dig_P7);
  Serial.print(",");
  Serial.print(a.dig_P8);
  Serial.print(",");
  Serial.print(a.dig_P9);

  Serial.print(",");
  Serial.print(a.dig_H1);
  Serial.print(",");
  Serial.print(a.dig_H2);
  Serial.print(",");
  Serial.print(a.dig_H3);
  Serial.print(",");
  Serial.print(a.dig_H4);
  Serial.print(",");
  Serial.print(a.dig_H5);
  Serial.print(",");
  Serial.print(a.dig_H6);

  // Independent calibration used by COHERENT
  Serial.print(",COH,");
  Serial.print(diagCal.T1);
  Serial.print(",");
  Serial.print(diagCal.T2);
  Serial.print(",");
  Serial.print(diagCal.T3);

  Serial.print(",");
  Serial.print(diagCal.P1);
  Serial.print(",");
  Serial.print(diagCal.P2);
  Serial.print(",");
  Serial.print(diagCal.P3);
  Serial.print(",");
  Serial.print(diagCal.P4);
  Serial.print(",");
  Serial.print(diagCal.P5);
  Serial.print(",");
  Serial.print(diagCal.P6);
  Serial.print(",");
  Serial.print(diagCal.P7);
  Serial.print(",");
  Serial.print(diagCal.P8);
  Serial.print(",");
  Serial.print(diagCal.P9);

  Serial.print(",");
  Serial.print(diagCal.H1);
  Serial.print(",");
  Serial.print(diagCal.H2);
  Serial.print(",");
  Serial.print(diagCal.H3);
  Serial.print(",");
  Serial.print(diagCal.H4);
  Serial.print(",");
  Serial.print(diagCal.H5);
  Serial.print(",");
  Serial.print(diagCal.H6);

  // Runtime state / physical registers
  Serial.print(",TFINE,");
  Serial.print(bme.diagnosticTFine());

  Serial.print(",CFG,");
  Serial.print(cfgOk ? 1 : 0);
  Serial.print(",");
  Serial.print(regs[0]);
  Serial.print(",");
  Serial.print(regs[1]);
  Serial.print(",");
  Serial.print(regs[2]);
  Serial.print(",");
  Serial.println(regs[3]);
}

unsigned long lastCalibrationTrace = 0;

// END ATMOSLINK DBG_CALTRACE

bool compensateCoherent(
    uint32_t adcT,
    uint32_t adcP,
    uint16_t adcH,
    float &temperature,
    float &humidity,
    float &pressure)
{
  if (!diagCal.valid)
    return false;

  int32_t var1;
  int32_t var2;
  int32_t tfine;

  var1 =
      ((int32_t)(adcT / 8) -
       ((int32_t)diagCal.T1 * 2));

  var1 =
      (var1 * ((int32_t)diagCal.T2)) /
      2048;

  var2 =
      ((int32_t)(adcT / 16) -
       ((int32_t)diagCal.T1));

  var2 =
      (((var2 * var2) / 4096) *
       ((int32_t)diagCal.T3)) /
      16384;

  tfine = var1 + var2;

  int32_t T =
      (tfine * 5 + 128) / 256;

  temperature = (float)T / 100.0F;

  int64_t pvar1;
  int64_t pvar2;
  int64_t pvar3;
  int64_t pvar4;

  pvar1 = ((int64_t)tfine) - 128000;

  pvar2 =
      pvar1 * pvar1 *
      (int64_t)diagCal.P6;

  pvar2 =
      pvar2 +
      ((pvar1 *
        (int64_t)diagCal.P5) *
       131072);

  pvar2 =
      pvar2 +
      (((int64_t)diagCal.P4) *
       34359738368LL);

  pvar1 =
      ((pvar1 * pvar1 *
        (int64_t)diagCal.P3) / 256) +
      ((pvar1 *
        (int64_t)diagCal.P2) *
       4096);

  pvar3 =
      ((int64_t)1) *
      140737488355328LL;

  pvar1 =
      (pvar3 + pvar1) *
      ((int64_t)diagCal.P1) /
      8589934592LL;

  if (pvar1 == 0)
    return false;

  pvar4 = 1048576 - adcP;

  pvar4 =
      (((pvar4 * 2147483648LL) -
        pvar2) * 3125) /
      pvar1;

  pvar1 =
      (((int64_t)diagCal.P9) *
       (pvar4 / 8192) *
       (pvar4 / 8192)) /
      33554432;

  pvar2 =
      (((int64_t)diagCal.P8) *
       pvar4) /
      524288;

  pvar4 =
      ((pvar4 + pvar1 + pvar2) / 256) +
      (((int64_t)diagCal.P7) * 16);

  pressure =
      ((float)pvar4 / 256.0F) /
      100.0F;

  int32_t hvar1;
  int32_t hvar2;
  int32_t hvar3;
  int32_t hvar4;
  int32_t hvar5;

  hvar1 =
      tfine - ((int32_t)76800);

  hvar2 =
      (int32_t)(adcH * 16384);

  hvar3 =
      (int32_t)(
          ((int32_t)diagCal.H4) *
          1048576);

  hvar4 =
      ((int32_t)diagCal.H5) *
      hvar1;

  hvar5 =
      (((hvar2 - hvar3) -
        hvar4) +
       (int32_t)16384) /
      32768;

  hvar2 =
      (hvar1 *
       ((int32_t)diagCal.H6)) /
      1024;

  hvar3 =
      (hvar1 *
       ((int32_t)diagCal.H3)) /
      2048;

  hvar4 =
      ((hvar2 *
        (hvar3 +
         (int32_t)32768)) /
       1024) +
      (int32_t)2097152;

  hvar2 =
      ((hvar4 *
        ((int32_t)diagCal.H2)) +
       8192) /
      16384;

  hvar3 = hvar5 * hvar2;

  hvar4 =
      ((hvar3 / 32768) *
       (hvar3 / 32768)) /
      128;

  hvar5 =
      hvar3 -
      ((hvar4 *
        ((int32_t)diagCal.H1)) /
       16);

  hvar5 =
      (hvar5 < 0 ? 0 : hvar5);

  hvar5 =
      (hvar5 > 419430400 ?
       419430400 : hvar5);

  uint32_t H =
      (uint32_t)(hvar5 / 4096);

  humidity =
      (float)H / 1024.0F;

  return true;
}

// END ATMOSLINK PRESS-Y4B

bool readBMERawADC(
    uint32_t &adcP,
    uint32_t &adcT,
    uint16_t &adcH)
{
  const uint8_t REG_PRESS_MSB = 0xF7;

  Wire.beginTransmission(ATMOSLINK_BME280_ADDRESS);
  Wire.write(REG_PRESS_MSB);

  if (Wire.endTransmission(false) != 0)
    return false;

  uint8_t n = Wire.requestFrom(
      (uint8_t)ATMOSLINK_BME280_ADDRESS,
      (uint8_t)8);

  if (n != 8)
    return false;

  uint8_t d[8];

  for (int i = 0; i < 8; i++)
  {
    if (!Wire.available())
      return false;

    d[i] = Wire.read();
  }

  adcP =
      ((uint32_t)d[0] << 12) |
      ((uint32_t)d[1] << 4) |
      ((uint32_t)d[2] >> 4);

  adcT =
      ((uint32_t)d[3] << 12) |
      ((uint32_t)d[4] << 4) |
      ((uint32_t)d[5] >> 4);

  adcH =
      ((uint16_t)d[6] << 8) |
      (uint16_t)d[7];

  return true;
}

bool readBMEDiagnostic(
    float &temperature,
    float &humidity,
    float &pressure)
{
  const int maxRetries = 5;

  for (int attempt = 1; attempt <= maxRetries; attempt++)
  {
    uint32_t rawP = 0;
    uint32_t rawT = 0;
    uint16_t rawH = 0;

    bool rawOk = readBMERawADC(
        rawP,
        rawT,
        rawH);

    float t = bme.readTemperature();
    float h = bme.readHumidity();
    float p = bme.readPressure() / 100.0F;

    float coherentT = NAN;
    float coherentH = NAN;
    float coherentP = NAN;

    bool coherentOk = false;

    if (rawOk)
    {
      coherentOk =
          compensateCoherent(
              rawT,
              rawP,
              rawH,
              coherentT,
              coherentH,
              coherentP);
    }

    // QA/QC PRESS-Y4B8C:
    // Adafruit se conserva exclusivamente para comparación diagnóstica.
    // La observación productiva utiliza una única captura cruda coherente.
    bool adafruitValid = validBME(t, h, p);

    bool coherentValid =
        rawOk &&
        coherentOk &&
        validBME(
            coherentT,
            coherentH,
            coherentP);

    Serial.print("INFO,DBG_COHERENT,");
    Serial.print(millis());
    Serial.print(",");
    Serial.print(attempt);
    Serial.print(",");
    Serial.print(rawOk ? 1 : 0);
    Serial.print(",");
    Serial.print(rawP);
    Serial.print(",");
    Serial.print(rawT);
    Serial.print(",");
    Serial.print(rawH);
    Serial.print(",");
    Serial.print(coherentOk ? 1 : 0);
    Serial.print(",");
    Serial.print(coherentT, 4);
    Serial.print(",");
    Serial.print(coherentH, 4);
    Serial.print(",");
    Serial.print(coherentP, 4);
    Serial.print(",");
    Serial.print(t, 4);
    Serial.print(",");
    Serial.print(h, 4);
    Serial.print(",");
    Serial.print(p, 4);
    Serial.print(",");
    Serial.println(adafruitValid ? 1 : 0);

    Serial.print("INFO,DBG_RAW,");
    Serial.print(millis());
    Serial.print(",");
    Serial.print(attempt);
    Serial.print(",");
    Serial.print(rawOk ? 1 : 0);
    Serial.print(",");
    Serial.print(rawP);
    Serial.print(",");
    Serial.print(rawT);
    Serial.print(",");
    Serial.print(rawH);
    Serial.print(",");
    Serial.print(t, 4);
    Serial.print(",");
    Serial.print(h, 4);
    Serial.print(",");
    Serial.println(p, 4);

    Serial.print("INFO,DBG_BME,");
    Serial.print(millis());
    Serial.print(",");
    Serial.print(attempt);
    Serial.print(",");
    Serial.print(t, 4);
    Serial.print(",");
    Serial.print(h, 4);
    Serial.print(",");
    Serial.print(p, 4);
    Serial.print(",");
    Serial.print(adafruitValid ? 1 : 0);
    Serial.print(",");
    Serial.println(sampleCount);

    if (coherentValid)
    {
      temperature = coherentT;
      humidity = coherentH;
      pressure = coherentP;
      return true;
    }

    rejectedCount++;
    delay(150);
  }

  return false;
}

void resetWindow()
{
  tempSum = 0.0;
  humSum = 0.0;
  presSum = 0.0;

  tempMin = 999.0;
  tempMax = -999.0;

  humMin = 999.0;
  humMax = -999.0;

  pressureMin = 9999.0;
  pressureMax = -9999.0;

  sampleCount = 0;
  rejectedCount = 0;
}

void pollRain(unsigned long now)
{
  if (now - lastRainPollTime < RAIN_POLL_MS)
    return;

  lastRainPollTime = now;

  int raw = digitalRead(RAIN_PIN);

  if (raw != rainRawLast)
  {
    rainRawLast = raw;
    rainRawChangedAt = now;
  }

  if ((now - rainRawChangedAt) >= RAIN_STABLE_MS &&
      raw != rainStableState)
  {
    rainStableState = raw;

    if (rainStableLast == HIGH &&
        rainStableState == LOW)
    {
      if (lastAcceptedTipTime == 0 ||
          now - lastAcceptedTipTime >= RAIN_MIN_TIP_MS)
      {
        rainTipsTotal++;
        rainTotalMM =
            rainTipsTotal * MM_PER_TIP;

        lastAcceptedTipTime = now;
      }
    }

    rainStableLast = rainStableState;
  }
}

void setup()
{
  Serial.begin(115200);

  delay(1000);

  Serial.println(
      "INFO,DBG_BOOT,CU01,V3_2_COHERENT_PROD");

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);

  pinMode(RAIN_PIN, INPUT_PULLUP);

  rainRawLast = digitalRead(RAIN_PIN);
  rainStableState = rainRawLast;
  rainStableLast = rainRawLast;

  bool bmeOK =
      bme.begin(ATMOSLINK_BME280_ADDRESS, &Wire);

  if (!bmeOK)
  {
    Serial.println(
        "ERROR,BME280_NOT_FOUND");

    while (true)
    {
      delay(1000);
    }
  }

  bool diagCalOk = loadDiagCalibration();

  Serial.print("INFO,DBG_CAL,");
  Serial.print(millis());
  Serial.print(",");
  Serial.print(diagCalOk ? 1 : 0);
  Serial.print(",");
  Serial.print(diagCal.T1);
  Serial.print(",");
  Serial.print(diagCal.T2);
  Serial.print(",");
  Serial.print(diagCal.T3);
  Serial.print(",");
  Serial.print(diagCal.P1);
  Serial.print(",");
  Serial.print(diagCal.P2);
  Serial.print(",");
  Serial.print(diagCal.P3);
  Serial.print(",");
  Serial.print(diagCal.P4);
  Serial.print(",");
  Serial.print(diagCal.P5);
  Serial.print(",");
  Serial.print(diagCal.P6);
  Serial.print(",");
  Serial.print(diagCal.P7);
  Serial.print(",");
  Serial.print(diagCal.P8);
  Serial.print(",");
  Serial.print(diagCal.P9);
  Serial.print(",");
  Serial.print(diagCal.H1);
  Serial.print(",");
  Serial.print(diagCal.H2);
  Serial.print(",");
  Serial.print(diagCal.H3);
  Serial.print(",");
  Serial.print(diagCal.H4);
  Serial.print(",");
  Serial.print(diagCal.H5);
  Serial.print(",");
  Serial.println(diagCal.H6);

  bme.setSampling(
      Adafruit_BME280::MODE_NORMAL,
      Adafruit_BME280::SAMPLING_X2,
      Adafruit_BME280::SAMPLING_X16,
      Adafruit_BME280::SAMPLING_X1,
      Adafruit_BME280::FILTER_X16,
      Adafruit_BME280::STANDBY_MS_500
  );

  resetWindow();

  lastSampleTime = millis();
  lastReadTime = millis();
}

void loop()
{
  if (
      millis() >= BME_WARMUP_MS &&
      (
          lastCalibrationTrace == 0 ||
          millis() - lastCalibrationTrace >= 30000UL
      )
  )
  {
    printCalibrationTrace();
    lastCalibrationTrace = millis();
  }

  unsigned long now = millis();

  pollRain(now);

  if (now < BME_WARMUP_MS)
    return;

  if (now - lastReadTime >= READ_INTERVAL_MS)
  {
    lastReadTime = now;

    float temperature;
    float humidity;
    float pressure;

    bool ok =
        readBMEDiagnostic(
            temperature,
            humidity,
            pressure);

    if (ok)
    {
      tempSum += temperature;
      humSum += humidity;
      presSum += pressure;

      if (temperature < tempMin)
        tempMin = temperature;

      if (temperature > tempMax)
        tempMax = temperature;

      if (humidity < humMin)
        humMin = humidity;

      if (humidity > humMax)
        humMax = humidity;

      if (pressure < pressureMin)
        pressureMin = pressure;

      if (pressure > pressureMax)
        pressureMax = pressure;

      sampleCount++;
    }
  }

  if (now - lastSampleTime >= SAMPLE_INTERVAL_MS)
  {
    lastSampleTime = now;

    float tempAvg = NAN;
    float humAvg = NAN;
    float presAvg = NAN;

    float dew = NAN;
    float vap = NAN;

    int bmeOk = 0;

    if (sampleCount > 0)
    {
      tempAvg = tempSum / sampleCount;
      humAvg = humSum / sampleCount;
      presAvg = presSum / sampleCount;

      dew = dewPoint(tempAvg, humAvg);
      vap = vaporPressure(tempAvg, humAvg);

      bmeOk = 1;
    }

    unsigned long tipsDelta =
        rainTipsTotal - lastTipsTotal;

    lastTipsTotal = rainTipsTotal;

    float rain1min =
        tipsDelta * MM_PER_TIP;

    Serial.print("INFO,DBG_MINUTE,");
    Serial.print(now);
    Serial.print(",");
    Serial.print(sampleCount);
    Serial.print(",");
    Serial.print(rejectedCount);
    Serial.print(",");
    Serial.print(pressureMin, 4);
    Serial.print(",");
    Serial.print(pressureMax, 4);
    Serial.print(",");
    Serial.print(presAvg, 4);
    Serial.print(",");
    Serial.print(humMin, 4);
    Serial.print(",");
    Serial.println(humMax, 4);

    /*
      NORMAL ATMOSLINK CSV — 17 CAMPOS

      t_s,
      temp_avg,
      temp_min,
      temp_max,
      hum_avg,
      hum_min,
      hum_max,
      pressure,
      dew_point,
      vapor_pressure,
      rain_1min,
      rain_1h,
      rain_total,
      pulses_delta,
      pulses_total,
      bme_ok,
      rain_ok
    */

    Serial.print(now / 1000);
    Serial.print(",");

    Serial.print(tempAvg, 2);
    Serial.print(",");
    Serial.print(tempMin, 2);
    Serial.print(",");
    Serial.print(tempMax, 2);
    Serial.print(",");

    Serial.print(humAvg, 2);
    Serial.print(",");
    Serial.print(humMin, 2);
    Serial.print(",");
    Serial.print(humMax, 2);
    Serial.print(",");

    Serial.print(presAvg, 2);
    Serial.print(",");

    Serial.print(dew, 2);
    Serial.print(",");
    Serial.print(vap, 2);
    Serial.print(",");

    Serial.print(rain1min, 2);
    Serial.print(",");

    /*
      rain_1h remains 0.00 here exactly as in the
      existing CU01 firmware candidate.
      AtmosLink performs higher-level aggregation.
    */
    Serial.print(0.00, 2);
    Serial.print(",");

    Serial.print(rainTotalMM, 2);
    Serial.print(",");

    Serial.print(tipsDelta);
    Serial.print(",");

    Serial.print(rainTipsTotal);
    Serial.print(",");

    Serial.print(bmeOk);
    Serial.print(",");

    Serial.println(1);

    resetWindow();
  }
}
