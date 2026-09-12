import logging
import os
import time
from pathlib import Path

import serial
from serial import SerialException

from weather_station.config.config import (
    LOG_FILE,
    RECONNECT_DELAY_SECONDS,
)
from weather_station.config.station_manager import get_station_context
from weather_station.acquisition.parser import parse_weather_line
from weather_station.database.sqlite_manager import init_db, insert_weather
from weather_station.database.csv_writer import init_csv, append_csv
from weather_station.acquisition.wind_sampler import WindSampler


STATION_CONTEXT = get_station_context()

SERIAL_PORT = (
    os.getenv("ATMOSLINK_SERIAL_PORT")
    or STATION_CONTEXT.get("serial_port")
    or "/dev/ttyUSB0"
)

BAUD_RATE = int(
    os.getenv("ATMOSLINK_SERIAL_BAUDRATE")
    or STATION_CONTEXT.get("serial_baudrate")
    or 115200
)

SERIAL_TIMEOUT = float(
    os.getenv("ATMOSLINK_SERIAL_TIMEOUT")
    or STATION_CONTEXT.get("serial_timeout")
    or 2
)

wind_enabled_env = os.getenv("ATMOSLINK_WIND_ENABLED")

if wind_enabled_env is None:
    WIND_REQUESTED = bool(
        STATION_CONTEXT.get("wind_enabled", False)
    )
else:
    WIND_REQUESTED = (
        wind_enabled_env.strip().lower()
        in {"1", "true", "yes", "on"}
    )

WIND_PORT = (
    os.getenv("ATMOSLINK_WIND_PORT")
    or STATION_CONTEXT.get("wind_port")
    or "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
).strip()

WIND_BAUDRATE = int(
    os.getenv("ATMOSLINK_WIND_BAUDRATE")
    or STATION_CONTEXT.get("wind_baudrate")
    or 9600
)

WIND_SLAVE_ID = int(
    os.getenv("ATMOSLINK_WIND_SLAVE_ID")
    or STATION_CONTEXT.get("wind_slave_id")
    or 1
)

WIND_START_REGISTER = int(
    os.getenv("ATMOSLINK_WIND_START_REGISTER")
    or STATION_CONTEXT.get("wind_start_register")
    or 0
)

WIND_QUANTITY = int(
    os.getenv("ATMOSLINK_WIND_QUANTITY")
    or STATION_CONTEXT.get("wind_quantity")
    or 10
)

WIND_TIMEOUT = float(
    os.getenv("ATMOSLINK_WIND_TIMEOUT")
    or STATION_CONTEXT.get("wind_timeout")
    or 2.0
)


WIND_SAMPLE_PERIOD = float(
    os.getenv("ATMOSLINK_WIND_SAMPLE_PERIOD")
    or 1.0
)

WIND_SAMPLER = None


_WIND_WARNING_STATE = {
    "reason": None,
    "timestamp": 0.0,
}

_SERIAL_WARNING_STATE = {
    "reason": None,
    "timestamp": 0.0,
}

ESP32_BOOT_PREFIXES = (
    "rst:",
    "ets ",
    "boot:",
    "configsip:",
    "clk_drv:",
    "mode:",
    "load:",
    "ho ",
    "entry ",
)

SERIAL_CONTROL_PREFIXES = (
    "INFO,",
    "WARN,",
    "ERROR,",
)

EXPECTED_WEATHER_FIELDS = 17


VALID_RANGES = {
    "temp_avg_C": (-30, 60),
    "temp_min_C": (-30, 60),
    "temp_max_C": (-30, 60),
    "hum_avg_pct": (0, 100),
    "hum_min_pct": (0, 100),
    "hum_max_pct": (0, 100),
    "pres_avg_hPa": (500, 1100),
    "dew_point_C": (-40, 60),
    "vapor_pressure_hPa": (0, 100),
    "rain_1min_mm": (0, 200),
    "rain_1h_mm": (0, 500),
    "rain_total_mm": (0, 100000),
    "pulses_delta": (0, 1000000),
    "pulses_total": (0, 1000000000),
    "wind_speed_ms": (0, 100),
    "wind_direction_deg": (0, 360),
    "wind_gust_ms": (0, 150),
    "bme_ok": (0, 1),
    "rain_ok": (0, 1),
    "wind_ok": (0, 1),
}


def setup_logging():
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def warn_serial_once(reason, interval_seconds=300):
    """
    Evita inundar systemd-journald cuando llegan tramas seriales
    corruptas, incompletas o no reconocidas.
    """
    now = time.monotonic()

    if (
        _SERIAL_WARNING_STATE["reason"] != reason
        or now - _SERIAL_WARNING_STATE["timestamp"] >= interval_seconds
    ):
        message = f"AVISO SERIAL: {reason}"
        print(message)
        logging.warning(reason)

        _SERIAL_WARNING_STATE["reason"] = reason
        _SERIAL_WARNING_STATE["timestamp"] = now


def is_serial_control_line(line):
    """
    Identifica mensajes informativos del firmware y mensajes de
    arranque del ESP32 que no representan observaciones científicas.
    """
    clean = line.strip()

    if not clean:
        return True

    return clean.startswith(
        ESP32_BOOT_PREFIXES + SERIAL_CONTROL_PREFIXES
    )


def is_weather_candidate(line):
    """
    Realiza una comprobación estructural preliminar antes de enviar
    la línea al parser meteorológico.
    """
    clean = line.strip()
    fields = [field.strip() for field in clean.split(",")]

    if len(fields) != EXPECTED_WEATHER_FIELDS:
        return False, (
            f"cantidad de campos inesperada: "
            f"{len(fields)}; se esperaban {EXPECTED_WEATHER_FIELDS}"
        )

    try:
        float(fields[0])
        float(fields[1])
    except (TypeError, ValueError):
        return False, "la trama no comienza con valores numéricos"

    return True, "ok"


def empty_wind_fields():
    """
    Devuelve campos de viento compatibles cuando el anemómetro
    no está disponible.
    """
    return {
        "wind_speed_ms": None,
        "wind_direction_deg": None,
        "wind_gust_ms": None,
        "wind_ok": 0,
    }


def warn_wind_once(reason, interval_seconds=300):
    """
    Evita repetir continuamente la misma advertencia relacionada
    con el anemómetro.
    """
    now = time.monotonic()

    if (
        _WIND_WARNING_STATE["reason"] != reason
        or now - _WIND_WARNING_STATE["timestamp"] >= interval_seconds
    ):
        print(f"AVISO VIENTO: {reason}")
        logging.warning(reason)

        _WIND_WARNING_STATE["reason"] = reason
        _WIND_WARNING_STATE["timestamp"] = now


def get_wind_availability():
    """
    Comprueba dinámicamente si el anemómetro puede utilizarse.

    Retorna:
        tuple[bool, str]: disponibilidad y motivo.
    """
    if not WIND_REQUESTED:
        return False, "módulo de viento deshabilitado por configuración"

    if not WIND_PORT:
        return False, "puerto de viento no configurado"

    if not os.path.exists(WIND_PORT):
        return False, f"anemómetro no detectado en {WIND_PORT}"

    weather_real = os.path.realpath(SERIAL_PORT)
    wind_real = os.path.realpath(WIND_PORT)

    if weather_real == wind_real:
        return (
            False,
            "conflicto de puertos: ESP32 y anemómetro apuntan "
            f"al mismo dispositivo ({weather_real})",
        )

    return True, "anemómetro disponible"


def get_wind_fields():
    """
    Obtiene un snapshot del muestreador continuo de viento.

    El hilo WindSampler es el único propietario lógico del RS485.
    Este método no abre el puerto serie.
    """
    global WIND_SAMPLER

    available, reason = get_wind_availability()

    if not available:
        if WIND_REQUESTED:
            warn_wind_once(reason)

        return empty_wind_fields()

    if WIND_SAMPLER is None:
        warn_wind_once("WindSampler no inicializado")
        return empty_wind_fields()

    try:
        reading = WIND_SAMPLER.snapshot_and_reset_gust()

        if reading.get("wind_ok") != 1:
            warn_wind_once(
                "WindSampler sin muestra reciente válida"
            )
        else:
            _WIND_WARNING_STATE["reason"] = None
            _WIND_WARNING_STATE["timestamp"] = 0.0

        return {
            "wind_speed_ms": reading.get("wind_speed_ms"),
            "wind_direction_deg": reading.get(
                "wind_direction_deg"
            ),
            "wind_gust_ms": reading.get("wind_gust_ms"),
            "wind_ok": reading.get("wind_ok", 0),
        }

    except Exception as exc:
        warn_wind_once(
            f"error obteniendo snapshot de viento: {exc}"
        )
        return empty_wind_fields()


def enrich_station_metadata(row):
    """
    Completa automáticamente los metadatos de la estación.

    Los valores enviados por el firmware se respetan cuando son
    válidos. Si vienen ausentes o como UNKNOWN, se reemplazan con
    la configuración local de la estación.
    """
    station_id = str(row.get("station_id") or "").strip()

    if not station_id or station_id.upper() == "UNKNOWN":
        row["station_id"] = STATION_CONTEXT["station_id"]

    station_name = str(row.get("station_name") or "").strip()

    if not station_name or station_name.upper() == "UNKNOWN":
        row["station_name"] = STATION_CONTEXT["station_name"]

    deployment_mode = str(
        row.get("deployment_mode") or ""
    ).strip()

    if not deployment_mode:
        row["deployment_mode"] = STATION_CONTEXT.get(
            "deployment_mode",
            "field",
        )

    firmware = str(row.get("firmware") or "").strip()

    if not firmware:
        row["firmware"] = "UNKNOWN"

    return row


def validate_weather_row(row):
    if not isinstance(row, dict):
        return False, "row no es diccionario"

    for field, (min_value, max_value) in VALID_RANGES.items():
        if field not in row:
            return False, f"campo ausente: {field}"

        value = row.get(field)

        if value is None:
            if field.startswith("wind_"):
                continue

            return False, f"valor nulo en {field}"

        try:
            value = float(value)
        except (TypeError, ValueError):
            return (
                False,
                f"valor no numérico en {field}: {row.get(field)}",
            )

        if value < min_value or value > max_value:
            return False, f"{field} fuera de rango: {value}"

    if row["temp_min_C"] > row["temp_avg_C"]:
        return False, "temp_min_C mayor que temp_avg_C"

    if row["temp_avg_C"] > row["temp_max_C"]:
        return False, "temp_avg_C mayor que temp_max_C"

    if row["hum_min_pct"] > row["hum_avg_pct"]:
        return False, "hum_min_pct mayor que hum_avg_pct"

    if row["hum_avg_pct"] > row["hum_max_pct"]:
        return False, "hum_avg_pct mayor que hum_max_pct"

    if (
        row["rain_1min_mm"] < 0
        or row["rain_1h_mm"] < 0
        or row["rain_total_mm"] < 0
    ):
        return False, "lluvia negativa"

    if row["pulses_delta"] < 0 or row["pulses_total"] < 0:
        return False, "pulsos negativos"

    return True, "ok"


def run_logger():
    global WIND_SAMPLER

    init_db()
    init_csv()

    wind_available, wind_reason = get_wind_availability()

    if WIND_REQUESTED and wind_available:
        WIND_SAMPLER = WindSampler(
            port=WIND_PORT,
            baudrate=WIND_BAUDRATE,
            slave_id=WIND_SLAVE_ID,
            timeout=min(WIND_TIMEOUT, 0.5),
            period=WIND_SAMPLE_PERIOD,
            stale_seconds=4.0,
        )

        WIND_SAMPLER.start()

        print(
            "WindSampler iniciado: "
            f"{WIND_SAMPLE_PERIOD:.1f} Hz nominal"
            if WIND_SAMPLE_PERIOD == 1.0
            else
            f"WindSampler iniciado: periodo "
            f"{WIND_SAMPLE_PERIOD:.2f} s"
        )

        logging.info(
            "WindSampler iniciado | periodo=%.3f s",
            WIND_SAMPLE_PERIOD,
        )

    print("Logger meteorológico iniciado")
    print(
        f"Estación: {STATION_CONTEXT['station_id']} | "
        f"{STATION_CONTEXT['station_name']}"
    )
    print(
        f"Modo: {STATION_CONTEXT.get('deployment_mode')}"
    )
    print(f"Puerto clima: {SERIAL_PORT}")
    print(f"Viento RS485 solicitado: {WIND_REQUESTED}")

    wind_available, wind_reason = get_wind_availability()

    print(
        f"Viento RS485 disponible al inicio: "
        f"{wind_available}"
    )
    print(f"Estado inicial del viento: {wind_reason}")

    if WIND_REQUESTED:
        print(
            f"Puerto viento configurado: {WIND_PORT}"
        )
        print(f"Baudrate viento: {WIND_BAUDRATE}")
        print(f"Slave ID viento: {WIND_SLAVE_ID}")

    logging.info(
        "Logger iniciado | estación=%s | puerto_clima=%s",
        STATION_CONTEXT["station_id"],
        SERIAL_PORT,
    )

    while True:
        try:
            print(f"Abriendo puerto {SERIAL_PORT}...")
            logging.info(f"Abriendo puerto {SERIAL_PORT}")

            with serial.Serial(
                port=SERIAL_PORT,
                baudrate=BAUD_RATE,
                timeout=SERIAL_TIMEOUT,
                write_timeout=SERIAL_TIMEOUT,
                rtscts=False,
                dsrdtr=False,
                xonxoff=False,
                exclusive=True,
            ) as ser:
                # El CP2102 puede accionar EN/BOOT mediante DTR y RTS.
                # Se mantienen ambas líneas inactivas para reducir
                # reinicios involuntarios del ESP32.
                try:
                    ser.setDTR(False)
                    ser.setRTS(False)
                except (AttributeError, OSError, SerialException) as exc:
                    logging.warning(
                        "No se pudo fijar DTR/RTS: %s",
                        exc,
                    )

                logging.info(
                    "Puerto serie abierto | puerto=%s | baudrate=%s",
                    SERIAL_PORT,
                    BAUD_RATE,
                )
                print(
                    f"Puerto serie abierto: "
                    f"{SERIAL_PORT} @ {BAUD_RATE} baud"
                )

                # Permite que el ESP32 termine un posible arranque.
                time.sleep(3)

                try:
                    ser.reset_input_buffer()
                    ser.reset_output_buffer()
                except (OSError, SerialException) as exc:
                    logging.warning(
                        "No se pudieron limpiar los buffers: %s",
                        exc,
                    )

                while True:
                    raw = ser.readline()

                    if not raw:
                        continue

                    try:
                        line = raw.decode(
                            "utf-8",
                            errors="strict",
                        ).strip()
                    except UnicodeDecodeError:
                        warn_serial_once(
                            "fragmento no UTF-8 descartado"
                        )
                        continue

                    if not line:
                        continue

                    if is_serial_control_line(line):
                        # Se registra como información, pero no se envía
                        # al parser meteorológico.
                        logging.info(
                            "Mensaje de control ESP32: %s",
                            line[:250],
                        )
                        continue

                    candidate, candidate_reason = (
                        is_weather_candidate(line)
                    )

                    if not candidate:
                        warn_serial_once(
                            f"{candidate_reason} | "
                            f"muestra={line[:120]!r}"
                        )
                        continue

                    # Se restablece el estado al recibir una trama
                    # estructuralmente válida.
                    _SERIAL_WARNING_STATE["reason"] = None
                    _SERIAL_WARNING_STATE["timestamp"] = 0.0

                    print("RX_VALIDO:", line)

                    try:
                        row = parse_weather_line(line)

                        if row is None:
                            continue

                        row = enrich_station_metadata(row)

                        wind_fields = get_wind_fields()
                        row.update(wind_fields)

                        valid, reason = validate_weather_row(row)

                        if not valid:
                            print(
                                "DATO INVALIDO DESCARTADO:",
                                reason,
                                row,
                            )
                            logging.warning(
                                "Dato invalido descartado: %s | "
                                "row=%s | raw=%s",
                                reason,
                                row,
                                line,
                            )
                            continue

                        row["firmware_version"] = (
                            STATION_CONTEXT.get("firmware_version")
                            or "UNKNOWN"
                        )
                        row["firmware_build"] = (
                            STATION_CONTEXT.get("firmware_build")
                            or "UNKNOWN"
                        )
                        row["device_id"] = (
                            STATION_CONTEXT.get("device_id")
                            or "UNKNOWN"
                        )

                        ts_utc, ts_local = insert_weather(row)
                        append_csv(
                            ts_utc,
                            ts_local,
                            row,
                        )

                        print(
                            "GUARDADO:",
                            ts_local,
                            row,
                        )
                        logging.info(
                            "Dato guardado: %s | estación=%s",
                            ts_local,
                            row["station_id"],
                        )

                    except Exception as exc:
                        print("Línea ignorada:", line)
                        logging.warning(
                            "Linea ignorada: %s | Error: %s",
                            line,
                            exc,
                        )

        except SerialException as exc:
            print(f"Error serial: {exc}")
            logging.error(f"Error serial: {exc}")
            print(
                f"Reintentando en "
                f"{RECONNECT_DELAY_SECONDS} segundos..."
            )
            time.sleep(RECONNECT_DELAY_SECONDS)

        except KeyboardInterrupt:
            print("Logger detenido por el usuario")
            logging.info("Logger detenido por el usuario")
            break

        except Exception as exc:
            print(f"Error general: {exc}")
            logging.error(f"Error general: {exc}")
            time.sleep(RECONNECT_DELAY_SECONDS)


if __name__ == "__main__":
    setup_logging()
    run_logger()
