import socket
import time

from io import BytesIO
from random import randint
from unittest import TestCase

from helper import (
    double_sha256,
    encode_varint,
    int_to_little_endian,
    little_endian_to_int,
    read_varint,
)


NETWORK_MAGIC = b'\xf9\xbe\xb4\xd9'
TESTNET_NETWORK_MAGIC = b'\x0b\x11\x09\x07'


class NetworkEnvelope:

    def __init__(self, command, payload, testnet=False):
        self.command = command
        self.payload = payload
        if testnet:
            self.magic = TESTNET_NETWORK_MAGIC
        else:
            self.magic = NETWORK_MAGIC

    def __repr__(self):
        return '{}: {}'.format(
            self.command.decode('ascii'),
            self.payload.hex(),
        )

    @classmethod
    def parse(cls, s, testnet=False):
        '''Takes a stream and creates a NetworkEnvelope'''
        # check the network magic
        magic = s.read(4)
        if magic == b'':
            raise RuntimeError('Connection reset!')
        if testnet:
            expected_magic = TESTNET_NETWORK_MAGIC
        else:
            expected_magic = NETWORK_MAGIC
        if magic != expected_magic:
            raise RuntimeError('magic is not right {} vs {}'.format(magic.hex(), expected_magic.hex()))
        # command 12 bytes
        # strip the trailing 0's
        # payload length 4 bytes, little endian
        # checksum 4 bytes, first four of double-sha256 of payload
        # payload is of length payload_length
        # verify checksum
        # return an instance of cls
        raise NotImplementedError

    def serialize(self):
        '''Returns the byte serialization of the entire network message'''
        # add the network magic
        # command 12 bytes (fill remaining bytes with 0's)
        # payload length 4 bytes, little endian
        # checksum 4 bytes, first four of double-sha256 of payload
        # payload
        raise NotImplementedError

    def stream(self):
        '''Returns a stream for parsing the payload'''
        return BytesIO(self.payload)


class NetworkEnvelopeTest(TestCase):

    def test_parse(self):
        msg = bytes.fromhex('f9beb4d976657261636b000000000000000000005df6e0e2')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        self.assertEqual(envelope.command, b'verack')
        self.assertEqual(envelope.payload, b'')
        msg = bytes.fromhex('f9beb4d976657273696f6e0000000000650000005f1a69d2721101000100000000000000bc8f5e5400000000010000000000000000000000000000000000ffffc61b6409208d010000000000000000000000000000000000ffffcb0071c0208d128035cbc97953f80f2f5361746f7368693a302e392e332fcf05050001')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        self.assertEqual(envelope.command, b'version')
        self.assertEqual(envelope.payload, msg[24:])

    def test_serialize(self):
        msg = bytes.fromhex('f9beb4d976657261636b000000000000000000005df6e0e2')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        self.assertEqual(envelope.serialize(), msg)
        msg = bytes.fromhex('f9beb4d976657273696f6e0000000000650000005f1a69d2721101000100000000000000bc8f5e5400000000010000000000000000000000000000000000ffffc61b6409208d010000000000000000000000000000000000ffffcb0071c0208d128035cbc97953f80f2f5361746f7368693a302e392e332fcf05050001')
        stream = BytesIO(msg)
        envelope = NetworkEnvelope.parse(stream)
        self.assertEqual(envelope.serialize(), msg)

        
class VersionMessage:

    def __init__(self, version=70015, services=0, timestamp=None,
                 receiver_services=0,
                 receiver_ip=b'\x00\x00\x00\x00', receiver_port=8333,
                 sender_services=0,
                 sender_ip=b'\x00\x00\x00\x00', sender_port=8333,
                 nonce=None, user_agent=b'/programmingblockchain:0.1/',
                 latest_block=0, relay=True):
        self.version = version
        self.services = services
        if timestamp is None:
            self.timestamp = int(time.time())
        else:
            self.timestamp = timestamp
        self.receiver_services = receiver_services
        self.receiver_ip = receiver_ip
        self.receiver_port = receiver_port
        self.sender_services = sender_services
        self.sender_ip = sender_ip
        self.sender_port = sender_port
        if nonce is None:
            self.nonce = int_to_little_endian(randint(0, 2**64), 8)
        else:
            self.nonce = nonce
        self.user_agent = user_agent
        self.latest_block = latest_block
        self.relay = relay

    def serialize(self):
        '''Serialize this message to send over the network'''
        # version is 4 bytes little endian
        # services is 8 bytes little endian
        # timestamp is 8 bytes little endian
        # receiver_services is 8 bytes little endian
        # IPV4 is b'\x00'*10+b'\xff'*2 then receiver_ip
        # receiver_port is 2 bytes, little endian
        # sender_services is 8 bytes little endian
        # IPV4 is b'\x00'*10+b'\xff'*2 then sender_ip
        # sender_port is 2 bytes, little endian
        # nonce should be 8 bytes
        # user_agent is a variable string, so varint first
        # latest_block is 4 bytes little endian
        # relay is 00 if false, 01 if true
        return NotImplementedError


class VersionMessageTest(TestCase):
    
    def test_serialize(self):
        v = VersionMessage(timestamp=0, nonce=b'\x00'*8)
        self.assertEqual(v.serialize().hex(), '7f11010000000000000000000000000000000000000000000000000000000000000000000000ffff000000008d20000000000000000000000000000000000000ffff000000008d2000000000000000001b2f70726f6772616d6d696e67626c6f636b636861696e3a302e312f0000000001')
    

class GetHeadersMessage:

    def __init__(self, version=70015, num_hashes=1, starting_block=None, ending_block=None):
        self.version = version
        self.num_hashes = num_hashes
        if starting_block is None:
            raise RuntimeError('a starting block is required')
        self.starting_block = starting_block
        if ending_block is None:
            self.ending_block = b'\x00' * 32
        else:
            self.ending_block = ending_block

    def serialize(self):
        '''Serialize this message to send over the network'''
        # version is 4 bytes little-endian
        # num_hashes is a varint
        # starting_block is in little-endian
        # ending_block is also in little-endian
        raise NotImplementedError

    
class GetHeadersMessageTest(TestCase):
    
    def test_serialize(self):
        block_hex = '0000000000000000001237f46acddf58578a37e213d2a6edc4884a2fcad05ba3'
        gh = GetHeadersMessage(starting_block=bytes.fromhex(block_hex))
        self.assertEqual(gh.serialize().hex(), '7f11010001a35bd0ca2f4a88c4eda6d213e2378a5758dfcd6af437120000000000000000000000000000000000000000000000000000000000000000000000000000000000')
    
    
class SimpleNode:
    
    def __init__(self, host, port=None, testnet=False, logging=False):
        if port is None:
            if testnet:
                port = 18333
            else:
                port = 8333
        self.testnet= testnet
        self.logging = logging
        # connect to socket
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        # create a stream that we can use with the rest of the library
        self.stream = self.socket.makefile('rb', None)

    def handshake(self):
        '''Do a handshake with the other node. Handshake is sending a version message and getting a verack back.'''
        # send a version message
        # wait for a verack message
        raise NotImplementedError
        
    def send(self, command, payload):
        '''Send a message to the connected node'''
        # create a network envelope
        envelope = NetworkEnvelope(command, payload, testnet=self.testnet)
        if self.logging:
            print('sending: {}'.format(envelope))
        # send the serialized envelope over the socket using sendall
        self.socket.sendall(envelope.serialize())
        
    def read(self):
        '''Read a message from the socket'''
        envelope = NetworkEnvelope.parse(self.stream, testnet=self.testnet)
        if self.logging:
            print('receiving: {}'.format(envelope))
        return envelope

    def wait_for_commands(self, commands):
        '''Wait for one of the commands in the list'''
        # initialize the command we have, which should be None
        command = None
        # loop until the command is in the commands we want
        while command not in commands:
            # get the next network message
            envelope = self.read()
            # set the command to be evaluated
            command = envelope.command
            # we know how to respond to version and ping, handle that here
            if command == b'version':
                # send verack
                self.send(b'verack', b'')
            elif command == b'ping':
                # send pong
                self.send(b'pong', envelope.payload)
        # return the last envelope we got
        return envelope
