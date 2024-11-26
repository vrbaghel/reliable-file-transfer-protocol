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
    chunk_size = homework5.MAX_PACKET - 8  # Reserve 4 bytes for header and 4 for checksum
    packets = []
    ack_times = {}  # Track packet sending times for RTT calculation

    # Prepare packets
    for i in range(0, len(data), chunk_size):
        seq_num = i // chunk_size
        header = struct.pack('!I', seq_num)
        payload = data[i:i + chunk_size]
        checksum = sum(header + payload) & 0xFFFFFFFF  # Simple checksum
        packets.append(header + struct.pack('!I', checksum) + payload)

    base = 0
    next_seq = 0
    window_size = 2
    estimated_rtt = 0.1
    dev_rtt = 0.05
    alpha, beta = 0.125, 0.25
    acked = set()

    while base < len(packets):
        while next_seq < base + window_size and next_seq < len(packets):
            if next_seq not in acked:
                sock.send(packets[next_seq])
                ack_times[next_seq] = time.time()
                logger.info(f"Sent packet {next_seq}")
            next_seq += 1

        try:
            timeout = estimated_rtt + 4 * dev_rtt
            sock.settimeout(timeout)
            ack = sock.recv(8)
            ack_seq = struct.unpack('!I', ack[:4])[0]
            logger.info(f"Received ACK for {ack_seq}")

            if ack_seq >= base:
                for seq in range(base, ack_seq + 1):
                    acked.add(seq)
                base = ack_seq + 1

            if ack_seq in ack_times:
                rtt_sample = time.time() - ack_times[ack_seq]
                estimated_rtt = (1 - alpha) * estimated_rtt + alpha * rtt_sample
                dev_rtt = (1 - beta) * dev_rtt + beta * abs(rtt_sample - estimated_rtt)

        except socket.timeout:
            logger.warning("Timeout occurred. Retransmitting.")
            next_seq = base

    final_packet = struct.pack('!I', 2**32 - 1) + struct.pack('!I', 0)
    sock.send(final_packet)
    logger.info("Sent final packet to signal completion.")


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
    received_packets = {}
    expected_seq = 0
    num_bytes = 0

    while True:
        try:
            packet = sock.recv(homework5.MAX_PACKET)
            if not packet:
                break

            seq_num = struct.unpack('!I', packet[:4])[0]
            checksum = struct.unpack('!I', packet[4:8])[0]
            payload = packet[8:]

            if seq_num == 2**32 - 1:
                logger.info("Received final packet. Ending reception.")
                break

            calculated_checksum = sum(packet[:4] + payload) & 0xFFFFFFFF
            if checksum != calculated_checksum:
                logger.warning(f"Checksum mismatch for packet {seq_num}. Dropping packet.")
                continue

            if seq_num not in received_packets:
                received_packets[seq_num] = payload

            ack = struct.pack('!I', seq_num)
            sock.send(ack)
            logger.info(f"Sent ACK for packet {seq_num}")

            while expected_seq in received_packets:
                dest.write(received_packets[expected_seq])
                num_bytes += len(received_packets[expected_seq])
                dest.flush()
                del received_packets[expected_seq]
                expected_seq += 1

        except socket.timeout:
            logger.warning("Timeout occurred while waiting for a packet.")
            continue

    return num_bytes

