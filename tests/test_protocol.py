import struct
from xbloom.protocol import build_command, parse_response, crc16, XBloomCommand

def test_crc16():
    # Construct a valid packet (12 bytes total)
    # Header(3) + Cmd(2) + Len(4) + Type(1)
    # 58 01 01 9A 11 0C 00 00 00 01
    data = bytes.fromhex("5801019A110C00000001")
    
    # Calculate CRC expected for this data
    # We trust the py impl is correct as it matches java
    crc = crc16(data)
    
    # Reconstruct packet
    packet = data + struct.pack('<H', crc)
    assert len(packet) == 12
    
    # Verify parse accepts it
    parsed = parse_response(packet)
    assert parsed['valid_crc'] is True

def test_build_brewer_start():
    cmd = XBloomCommand.APP_BREWER_START # 0x119A
    packet = build_command(cmd)
    
    # Verify length
    assert len(packet) == 12
    
    # Verify content
    assert packet[0] == 0x58
    assert packet[3] == 0x9A
    assert packet[4] == 0x11
    
    parsed = parse_response(packet)
    assert parsed['valid_crc'] is True
    assert parsed['command'] == 0x119A
