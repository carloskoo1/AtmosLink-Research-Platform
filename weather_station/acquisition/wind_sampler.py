import logging
import threading
import time
from collections import deque
from statistics import mean

from weather_station.acquisition.wind_rs485 import read_wind


class WindSampler:
    """
    Muestreador continuo del anemómetro RS485.

    Metodología:
    - adquisición nominal a 1 Hz;
    - media móvil de 3 muestras (~3 s);
    - ráfaga = máximo de las medias móviles de 3 s
      dentro de la ventana entre observaciones meteorológicas.

    El hilo es el único consumidor del puerto RS485.
    """

    def __init__(
        self,
        port,
        baudrate=9600,
        slave_id=1,
        timeout=0.5,
        period=1.0,
        stale_seconds=4.0,
    ):
        self.port = port
        self.baudrate = baudrate
        self.slave_id = slave_id
        self.timeout = timeout
        self.period = period
        self.stale_seconds = stale_seconds

        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._thread = None

        self._last_speed = None
        self._last_direction = None
        self._last_sample_monotonic = None

        self._speed_window = deque(maxlen=3)

        self._gust_max = None
        self._gust_samples = 0

        self._total_samples = 0
        self._total_errors = 0
        self._last_error = None

    def start(self):
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()

        self._thread = threading.Thread(
            target=self._run,
            name="AtmosLinkWindSampler",
            daemon=True,
        )

        self._thread.start()

    def stop(self):
        self._stop_event.set()

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3.0)

    def _run(self):
        next_cycle = time.monotonic()

        while not self._stop_event.is_set():

            try:
                reading = read_wind(
                    port=self.port,
                    baudrate=self.baudrate,
                    slave_id=self.slave_id,
                    timeout=self.timeout,
                )

                now = time.monotonic()

                if reading.get("wind_ok") == 1:

                    speed = reading.get("wind_speed_ms")
                    direction = reading.get("wind_direction_deg")

                    if speed is not None and direction is not None:

                        speed = float(speed)
                        direction = float(direction)

                        with self._lock:

                            self._last_speed = speed
                            self._last_direction = direction
                            self._last_sample_monotonic = now

                            self._speed_window.append(speed)

                            self._total_samples += 1
                            self._last_error = None

                            if len(self._speed_window) == 3:

                                avg3 = mean(self._speed_window)

                                self._gust_samples += 1

                                if (
                                    self._gust_max is None
                                    or avg3 > self._gust_max
                                ):
                                    self._gust_max = avg3

                else:

                    with self._lock:
                        self._total_errors += 1
                        self._last_error = reading.get(
                            "wind_error",
                            "lectura_no_valida",
                        )

            except Exception as exc:

                with self._lock:
                    self._total_errors += 1
                    self._last_error = str(exc)

                logging.warning(
                    "WindSampler: error RS485: %s",
                    exc,
                )

            next_cycle += self.period

            delay = next_cycle - time.monotonic()

            if delay > 0:
                self._stop_event.wait(delay)
            else:
                # Si excepcionalmente una lectura demora más del periodo,
                # se reanuda desde el tiempo actual sin acumular retraso.
                next_cycle = time.monotonic()

    def snapshot_and_reset_gust(self):
        """
        Devuelve la última velocidad/dirección válida y la ráfaga
        máxima calculada durante la ventana actual.

        Después de entregar la ráfaga comienza una nueva ventana.
        """

        now = time.monotonic()

        with self._lock:

            fresh = (
                self._last_sample_monotonic is not None
                and
                now - self._last_sample_monotonic
                <= self.stale_seconds
            )

            if fresh:
                speed = self._last_speed
                direction = self._last_direction
                wind_ok = 1
            else:
                speed = None
                direction = None
                wind_ok = 0

            # Solo se publica ráfaga si existió al menos una
            # media móvil válida de tres muestras.
            if fresh and self._gust_samples > 0:
                gust = self._gust_max
            else:
                gust = None

            result = {
                "wind_speed_ms": speed,
                "wind_direction_deg": direction,
                "wind_gust_ms": gust,
                "wind_ok": wind_ok,
                "wind_sampler_samples": self._total_samples,
                "wind_sampler_errors": self._total_errors,
                "wind_sampler_error": self._last_error,
            }

            # Comienza nueva ventana de ráfaga.
            # NO borramos speed_window porque la media móvil debe
            # permanecer temporalmente continua entre ventanas.
            self._gust_max = None
            self._gust_samples = 0

            return result
