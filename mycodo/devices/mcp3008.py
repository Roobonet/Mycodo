# coding=utf-8
import argparse
import logging
from time import sleep

import Adafruit_MCP3008
import locket
import os


class MCP3008Read(object):
    """ ADC Read """
    def __init__(self, input_dev, testing=False):
        self.logger = logging.getLogger('mycodo.mcp3008')
        self._voltage = None
        self.adc = None

        self.pin_clock = input_dev.pin_clock
        self.pin_cs = input_dev.pin_cs
        self.pin_miso = input_dev.pin_miso
        self.pin_mosi = input_dev.pin_mosi
        self.adc_channel = input_dev.adc_channel
        self.adc_volts_max = input_dev.adc_volts_max

        self.lock_file = '/var/lock/mcp3008-{clock}-{cs}-{miso}-{mosi}'.format(
            clock=self.pin_clock, cs=self.pin_cs,
            miso=self.pin_miso, mosi=self.pin_mosi)

        if not testing:
            self.logger = logging.getLogger(
                'mycodo.mcp3008_{id}'.format(id=input_dev.id))
            self.adc = Adafruit_MCP3008.MCP3008(clk=self.pin_clock,
                                                cs=self.pin_cs,
                                                miso=self.pin_miso,
                                                mosi=self.pin_mosi)

    def read(self):
        """ Take a measurement """
        self._voltage = None
        lock_acquired = False
        try:
            # Set up lock
            lock = locket.lock_file(self.lock_file, timeout=120)
            try:
                lock.acquire()
                lock_acquired = True
            except:
                self.logger.error("Could not acquire lock. Breaking for future locking.")
                os.remove(self.lock_file)

            if lock_acquired:
                sleep(0.1)
                self._voltage = (self.adc.read_adc(self.adc_channel) / 1023.0) * self.adc_volts_max
                lock.release()
        except Exception as e:
            self.logger.exception(
                "{cls} raised exception during read(): "
                "{err}".format(cls=type(self).__name__, err=e))
            return 1

    @property
    def voltage(self):
        return self._voltage

    def __iter__(self):
        """
        Support the iterator protocol.
        """
        return self

    def next(self):
        """
        Call the read method and return voltage information.
        """
        if self.read():
            return None
        return dict(voltage=float('{0:.4f}'.format(self._voltage)))


def parse_args(parser):
    """ Add arguments for argparse """
    parser.add_argument('--clockpin', metavar='CLOCKPIN', type=int,
                        help='SPI Clock Pin',
                        required=True)
    parser.add_argument('--misopin', metavar='MISOPIN', type=int,
                        help='SPI MISO Pin',
                        required=True)
    parser.add_argument('--mosipin', metavar='MOSIPIN', type=int,
                        help='SPI MOSI Pin',
                        required=True)
    parser.add_argument('--cspin', metavar='CSPIN', type=int,
                        help='SPI CS Pin',
                        required=True)
    parser.add_argument('--adcchannel', metavar='ADCCHANNEL', type=int,
                        help='channel to read from the ADC (0 - 7)',
                        required=False, choices=range(0,8))
    return parser.parse_args()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='MCP3008 Analog-to-Digital Converter Read Test Script')
    args = parse_args(parser)

    # Example Software SPI pins: CLK = 18, MISO = 23, MOSI = 24, CS = 25
    mcp = Adafruit_MCP3008.MCP3008(clk=args.clockpin,
                                   cs=args.cspin,
                                   miso=args.misopin,
                                   mosi=args.mosipin)

    if -1 < args.adcchannel < 8:
        # Read the specified channel
        value = mcp.read_adc(args.adcchannel)
        print("ADC Channel: {chan}, Output: {out}".format(
            chan=args.adcchannel, out=value))
    else:
        # Create a list for the ADC channel values
        values = [0] * 8

        # Conduct measurements of channels 0 - 7, add them to the list
        for i in range(8):
            values[i] = mcp.read_adc(i)

        # Print the list of ADC values
        print('| {0:>4} | {1:>4} | {2:>4} | {3:>4} | {4:>4} | {5:>4} | {6:>4} | {7:>4} |'.format(*values))
