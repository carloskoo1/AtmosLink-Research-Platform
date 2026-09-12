import time
import serial


DEFAULT_PORT = "/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0"
DEFAULT_BAUDRATE = 9600
DEFAULT_SLAVE_ID = 1
DEFAULT_TIMEOUT = 2

DIRECTIONS_16 = {
    0: ("N", 0.0),
    1: ("NNE", 22.5),
    2: ("NE", 45.0),
    3: ("ENE", 67.5),
    4: ("E", 90.0),
    5: ("ESE", 112.5),
    6: ("SE", 135.0),
    7: ("SSE", 157.5),
    8: ("S", 180.0),
    9: ("SSW", 202.5),
    10: ("SW", 225.0),
    11: ("WSW", 247.5),
    12: ("W", 270.0),
    13: ("WNW", 292.5),
    14: ("NW", 315.0),
    15: ("NNW", 337.5),
}


def crc16_modbus(data: bytes) -> int:
    crc = 0xFFFF

    for byte in data:
        crc ^= byte

        for _ in range(8):
            if crc & 1:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc >>= 1

    return crc


def build_read_holding_registers_request(slave_id: int, address: int, count: int) -> bytes:
    frame = bytes([
        slave_id,
        0x03,
        (address >> 8) & 0xFF,
        address & 0xFF,
        (count >> 8) & 0xFF,
        count & 0xFF,
    ])

    crc = crc16_modbus(frame)

    return frame + bytes([
        crc & 0xFF,
        (crc >> 8) & 0xFF,
    ])


def validate_crc(response: bytes) -> bool:
    if len(response) < 5:
        return False

    payload = response[:-2]
    received_crc = response[-2] | (response[-1] << 8)
    calculated_crc = crc16_modbus(payload)

    return received_crc == calculated_crc


def parse_registers(response: bytes):
    if len(response) < 5:
        raise ValueError("Respuesta Modbus demasiado corta")

    slave_id = response[0]
    function = response[1]
    byte_count = response[2]

    if function != 0x03:
        raise ValueError(f"Función Modbus inesperada: {function}")

    expected_len = 3 + byte_count + 2

    if len(response) < expected_len:
        raise ValueError(
            f"Respuesta incompleta: recibido={len(response)}, esperado={expected_len}"
        )

    response = response[:expected_len]

    if not validate_crc(response):
        raise ValueError("CRC Modbus inválido")

    data = response[3:3 + byte_count]

    if len(data) % 2 != 0:
        raise ValueError("Cantidad inválida de bytes de datos")

    registers = []

    for i in range(0, len(data), 2):
        registers.append((data[i] << 8) | data[i + 1])

    return slave_id, registers


def read_wind(
    port: str = DEFAULT_PORT,
    baudrate: int = DEFAULT_BAUDRATE,
    slave_id: int = DEFAULT_SLAVE_ID,
    timeout: float = DEFAULT_TIMEOUT,
):
    request = build_read_holding_registers_request(
        slave_id=slave_id,
        address=0,
        count=10,
    )

    with serial.Serial(
        port=port,
        baudrate=baudrate,
        bytesize=8,
        parity="N",
        stopbits=1,
        timeout=timeout,
    ) as ser:
        ser.reset_input_buffer()
        ser.reset_output_buffer()

        ser.write(request)
        ser.flush()

        # La respuesta Modbus RTU se lee según la longitud indicada
        # por su propia cabecera. Evita esperar innecesariamente
        # hasta agotar el timeout con ser.read(64).
        header = ser.read(3)

        if len(header) != 3:
            response = b""
        else:
            byte_count = header[2]
            body = ser.read(byte_count + 2)

            if len(body) != byte_count + 2:
                response = b""
            else:
                response = header + body

    if not response:
        return {
            "wind_speed_ms": None,
            "wind_speed_kmh": None,
            "wind_direction_deg": None,
            "wind_direction_text": None,
            "wind_sector_code": None,
            "wind_gust_ms": None,
            "wind_ok": 0,
            "wind_error": "sin_respuesta",
            "wind_raw_registers": None,
        }

    _, registers = parse_registers(response)

    if len(registers) < 9:
        raise ValueError(
            f"Registros insuficientes: {registers}"
        )

    # Mapa validado experimentalmente para este anemómetro:
    # R00 = velocidad en décimas de m/s
    # R02 = velocidad en centésimas de km/h
    # R03 = dirección en décimas de grado
    # R04 = sector cardinal codificado de 0 a 15
    speed_ms = registers[0] / 10.0
    speed_kmh = registers[2] / 100.0
    direction_deg = registers[3] / 10.0
    sector_code = registers[4]

    direction_text, sector_reference_deg = DIRECTIONS_16.get(
        sector_code,
        ("UNKNOWN", None),
    )

    wind_ok = 1
    wind_error = None

    if not 0.0 <= speed_ms <= 60.0:
        wind_ok = 0
        wind_error = f"velocidad_fuera_de_rango:{speed_ms}"

    if not 0.0 <= direction_deg <= 360.0:
        wind_ok = 0
        wind_error = f"direccion_fuera_de_rango:{direction_deg}"

    if sector_reference_deg is None:
        wind_ok = 0
        wind_error = f"sector_desconocido:{sector_code}"

    return {
        "wind_speed_ms": round(speed_ms, 2),
        "wind_speed_kmh": round(speed_kmh, 2),
        "wind_direction_deg": round(direction_deg, 1),
        "wind_direction_text": direction_text,
        "wind_sector_code": sector_code,
        "wind_gust_ms": None,
        "wind_ok": wind_ok,
        "wind_error": wind_error,
        "wind_raw_registers": registers,
    }


if __name__ == "__main__":
    result = read_wind()
    print(result)
