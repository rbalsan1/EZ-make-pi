# SPDX-FileCopyrightText: 2017 Radomir Dopieralski for Adafruit
# Industries
#
# SPDX-License-Identifier: MIT
""" MAX6675 this is a modification of the circuit python driver for the
adafruit_max31855 meant to run the max6675 Author: Bobbi Balsano
``adafruit_max31855`` =========================== This is a
CircuitPython driver for the Maxim Integrated MAX31855 thermocouple
amplifier module. * Author(s): Radomir Dopieralski Implementation Notes
-------------------- **Hardware:** * Adafruit `MAX31855 Thermocouple
Amplifier Breakout
  <https://www.adafruit.com/product/269>`_ (Product ID: 269) **Software
and Dependencies:** * Adafruit CircuitPython firmware for the ESP8622
and M0-based boards:
  https://github.com/adafruit/circuitpython/releases * Adafruit's Bus
Device library:
https://github.com/adafruit/Adafruit_CircuitPython_BusDevice """
import math
try:
    import struct
except ImportError:
    import ustruct as struct
from adafruit_bus_device.spi_device import SPIDevice
__version__ ="0.0.0-auto.0"
class MAX6675:
    """ Driver for the MAX6675 thermocouple amplifier. """
    def    __init__(self, spi, cs):
        self.spi_device = SPIDevice(spi, cs)
        self.data = bytearray(2)
    def _read(self):
        with self.spi_device as spi:
            spi.readinto(self.data) # pylint: disable=no-member
        if self.data[1] & 0x04: 
            raise RuntimeError("thermocouple not connected")
        temp = self.data[0]<<8 | self.data[1] #struct.unpack("h", self.data) 
        temp >>= 3 
        return temp / 4
    @property 
    def temperature(self):
        """Thermocouple temperature in degrees Celsius."""
        return self._read()
