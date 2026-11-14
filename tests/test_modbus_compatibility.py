"""Verify that installed pymodbus and hoymiles_modbus are able to read data from a (fake) DTU.

The other tests mock the Modbus client, so they do not detect an incompatible version of pymodbus.
"""

import socket
import struct
import threading

import pytest
from hoymiles_modbus.client import HoymilesModbusTCP

DTU_SERIAL = '4121a021abeb'
# serial number, port number, today production, total production
PORTS = [('1410a01d0001', 1, 111, 900001), ('1410a01d0001', 2, 222, 900002), ('1410a01d0002', 1, 333, 900003)]
INVERTER_REGISTERS_START = 0x1000
DTU_SERIAL_REGISTERS_START = 0x2000
INVERTER_RECORD_SIZE = 40


def _get_inverter_record(serial: str, port: int, today_production: int, total_production: int) -> bytes:
    record = struct.pack(
        '>B6sBHHHHHHIhHHHB',
        0x0C,
        bytes.fromhex(serial),
        port,
        345,  # pv_voltage
        812,  # pv_current
        2301,  # grid_voltage
        5001,  # grid_frequency
        2805,  # pv_power
        today_production,
        total_production,
        251,  # temperature
        3,  # operating_status
        0,  # alarm_code
        0,  # alarm_count
        1,  # link_status
    )
    return record.ljust(INVERTER_RECORD_SIZE, b'\0')


def _get_registers(address: int, count: int) -> bytes:
    if address == DTU_SERIAL_REGISTERS_START:
        return bytes.fromhex(DTU_SERIAL)[: count * 2]
    index, offset = divmod(address - INVERTER_REGISTERS_START, INVERTER_RECORD_SIZE)
    record = _get_inverter_record(*PORTS[index]) if index < len(PORTS) else bytes(INVERTER_RECORD_SIZE)
    return record[offset * 2 : (offset + count) * 2]


def _receive(connection: socket.socket, size: int) -> bytes:
    data = b''
    while len(data) < size:
        chunk = connection.recv(size - len(data))
        if not chunk:
            raise ConnectionError
        data += chunk
    return data


def _serve(server: socket.socket, wrong_byte_count: bool) -> None:
    while True:
        try:
            connection, _ = server.accept()
        except OSError:
            return
        try:
            while True:
                transaction_id, protocol_id, length, unit_id = struct.unpack('>HHHB', _receive(connection, 7))
                function_code, address, count = struct.unpack('>BHH', _receive(connection, length - 1))
                registers = _get_registers(address, count)
                byte_count = 0 if wrong_byte_count else len(registers)
                pdu = struct.pack('>BB', function_code, byte_count) + registers
                connection.sendall(struct.pack('>HHHB', transaction_id, protocol_id, len(pdu) + 1, unit_id) + pdu)
        except (ConnectionError, OSError):
            connection.close()


@pytest.mark.parametrize('wrong_byte_count', [False, True])
def test_read_plant_data_from_fake_dtu(wrong_byte_count):
    """Read plant data from a fake DTU, also from one sending a wrong byte count (as some DTUs do)."""
    with socket.socket() as server:
        server.bind(('127.0.0.1', 0))
        server.listen()
        threading.Thread(target=_serve, args=(server, wrong_byte_count), daemon=True).start()
        modbus_client = HoymilesModbusTCP(host='127.0.0.1', port=server.getsockname()[1])
        modbus_client.comm_params.timeout = 1
        modbus_client.comm_params.retries = 0

        plant_data = modbus_client.plant_data

    assert plant_data.dtu == DTU_SERIAL
    assert [
        (inverter.serial_number, inverter.port_number, inverter.today_production, inverter.total_production)
        for inverter in plant_data.inverters
    ] == PORTS
    assert plant_data.today_production == 666
    assert plant_data.total_production == 2700006
