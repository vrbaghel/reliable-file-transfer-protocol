"""
Where solution code to HW5 should be written.  No other files should
be modified.
"""

import socket
import io
import time
import typing
import struct
import homework5
import homework5.logging


def send(sock: socket.socket, data: bytes):
    """
    Implementation of the sending logic for sending data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.
        data -- A bytes object, containing the data to send over the network.
    """

    # Naive implementation where we chunk the data to be sent into
    # packets as large as the network will allow, and then send them
    # over the network, pausing half a second between sends to let the
    # network "rest" :)
    logger = homework5.logging.get_logger("hw5-sender")
    MAX_SEQ = 2  # Maximum sequence numbers (0 and 1)
    seq_num = 0  # Sequence number of the next packet to send
    base = 0  # Oldest unacknowledged packet
    packet_queue = []  # Packets in flight
    chunk_size = homework5.MAX_PACKET - 8  # Adjust for header size
    offsets = range(0, len(data), chunk_size)

    # Prepare packets
    packets = []
    for i, chunk in enumerate(data[i:i + chunk_size] for i in offsets):
        header = struct.pack('!I', i % MAX_SEQ)  # Sequence number
        packets.append(header + chunk)

    estimated_rtt = 0.1
    dev_rtt = 0.01

    while base < len(packets):
        # Send packets within the window
        while seq_num < base + 2 and seq_num < len(packets):
            sock.send(packets[seq_num])
            logger.info(f"Sent packet {seq_num % MAX_SEQ}")
            seq_num += 1

        # Wait for ACKs
        try:
            sock.settimeout(estimated_rtt + 4 * dev_rtt)
            ack = sock.recv(8)
            ack_seq = struct.unpack('!I', ack[:4])[0]
            logger.info(f"Received ACK for {ack_seq}")

            # Slide window
            if ack_seq == base % MAX_SEQ:
                base += 1

        except socket.timeout:
            logger.warning(f"Timeout for packet {base % MAX_SEQ}, retransmitting")
            seq_num = base  # Retransmit from the base of the window


def recv(sock: socket.socket, dest: io.BufferedIOBase) -> int:
    """
    Implementation of the receiving logic for receiving data over a slow,
    lossy, constrained network.

    Args:
        sock -- A socket object, constructed and initialized to communicate
                over a simulated lossy network.

    Return:
        The number of bytes written to the destination.
    """
    logger = homework5.logging.get_logger("hw5-receiver")
    expected_seq = 0
    num_bytes = 0

    while True:
        try:
            packet = sock.recv(homework5.MAX_PACKET)
            if not packet:
                break

            seq_num = struct.unpack('!I', packet[:4])[0]
            data = packet[4:]

            # Only accept in-order packets
            if seq_num == expected_seq:
                dest.write(data)
                dest.flush()
                num_bytes += len(data)
                expected_seq = (expected_seq + 1) % 2

            # Send ACK
            ack = struct.pack('!I', seq_num)
            sock.send(ack)
            logger.info(f"Sent ACK for {seq_num}")

        except socket.timeout:
            logger.warning("Socket timeout, waiting for data")

    return num_bytes
