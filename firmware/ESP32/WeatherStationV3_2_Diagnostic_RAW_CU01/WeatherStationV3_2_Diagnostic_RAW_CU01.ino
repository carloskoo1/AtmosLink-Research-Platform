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

#define BME280_ADDRESS 0x76

const float MM_PER_TIP = 0.2794;

const unsigned long SAMPLE_INTERVAL_MS = 60000;
const unsigned long READ_INTERVAL_MS   = 5000;
const unsigned long BME_WARMUP_MS      = 30000;

const unsigned long RAIN_POLL_MS       = 20;
const unsigned long RAIN_STABLE_MS     = 80;
const unsigned long RAIN_MIN_TIP_MS    = 2000;

Adafruit_BME280 bme;

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
bool readBMERawADC(
    uint32_t &adcP,
    uint32_t &adcT,
    uint16_t &adcH)
{
  const uint8_t REG_PRESS_MSB = 0xF7;

  Wire.beginTransmission(BME280_ADDRESS);
  Wire.write(REG_PRESS_MSB);

  if (Wire.endTransmission(false) != 0)
    return false;

  uint8_t n = Wire.requestFrom(
      (uint8_t)BME280_ADDRESS,
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

    bool valid = validBME(t, h, p);

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
    Serial.print(valid ? 1 : 0);
    Serial.print(",");
    Serial.println(sampleCount);

    if (valid)
    {
      temperature = t;
      humidity = h;
      pressure = p;
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
      "INFO,DBG_BOOT,CU01,V3_2_DIAG");

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(100000);

  pinMode(RAIN_PIN, INPUT_PULLUP);

  rainRawLast = digitalRead(RAIN_PIN);
  rainStableState = rainRawLast;
  rainStableLast = rainRawLast;

  bool bmeOK =
      bme.begin(BME280_ADDRESS, &Wire);

  if (!bmeOK)
  {
    Serial.println(
        "ERROR,BME280_NOT_FOUND");

    while (true)
    {
      delay(1000);
    }
  }

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
