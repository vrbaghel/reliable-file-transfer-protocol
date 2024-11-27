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

    logger.info(f"Sending {len(packets)} packets.")

    # We keep track of the 'base' sequence number and the 'next_seq'
    # sequence number.  The 'base' sequence number is the sequence number
    # of the first packet in the window, and the 'next_seq' sequence number
    # is the sequence number of the next packet to be sent.  The window
    # starts at 'base' and ends at 'next_seq'.
    base = 0
    next_seq = 0
    window_size = 2
    estimated_rtt = 0.5 # Estimated round trip time.
    dev_rtt = 0.1 # Deviation of round trip time.
    alpha, beta = 0.125, 0.25 # The alpha and beta parameters for the EWMA algorithm.
    acked = set() # Set of packets that have been acknowledged.

    while base < len(packets):
        while next_seq < base + window_size and next_seq < len(packets):
            if next_seq not in acked:
                sock.send(packets[next_seq])
                ack_times[next_seq] = time.time()
                logger.info(f"Sent packet {next_seq}")
            next_seq += 1

        try:
            # Set the socket timeout to the estimated RTT + 4 * deviation
            # to ensure that we wait long enough for the packets to be
            # acknowledged.
            timeout = estimated_rtt + 4 * dev_rtt
            sock.settimeout(timeout)
            ack = sock.recv(4)
            logger.info(f"Received ACK: {ack}")
            ack_seq = struct.unpack('!I', ack)[0]
            logger.info(f"Received ACK for {ack_seq}")

            if ack_seq >= base:
                # If we received an ACK for a packet that is in our window,
                # slide the window forward and update the base.
                prev_ack = all(seq in acked for seq in range(base, ack_seq))
                if prev_ack:
                  acked.add(ack_seq)
                  base = ack_seq + 1

            if ack_seq in ack_times:
                # Calculate the RTT sample and update the estimated RTT and
                # deviation.
                rtt_sample = time.time() - ack_times[ack_seq]
                estimated_rtt = (1 - alpha) * estimated_rtt + alpha * rtt_sample
                dev_rtt = (1 - beta) * dev_rtt + beta * abs(rtt_sample - estimated_rtt)

        except socket.timeout:
            logger.warning("Timeout occurred. Retransmitting.")
            # If a timeout occurs, increase the estimated RTT
            # so that we wait longer for the packets to be acknowledged.
            # estimated_rtt += 0.5
            # Go back to the base of the window and start again.
            next_seq = base
            # Remove any packets that have already been acknowledged after the base
            logger.info(f"**** Acked: {acked}, base: {base} ****")
            acked = {seq for seq in acked if seq < next_seq}

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
    received_packets = {}  # Dictionary to store packets by their sequence number
    expected_seq = 0  # The next expected sequence number
    num_bytes = 0  # Total number of bytes written to the destination

    while True:
        try:
            # Receive a packet from the socket
            packet = sock.recv(homework5.MAX_PACKET)
            if not packet:
                break  # Exit if no more data is received

            # Extract sequence number, checksum, and payload from the packet
            seq_num = struct.unpack('!I', packet[:4])[0]
            checksum = struct.unpack('!I', packet[4:8])[0]
            payload = packet[8:]

            # Check for the final packet, which signals completion
            if seq_num == 2**32 - 1:
                logger.info("Received final packet. Ending reception.")
                break

            # Verify the checksum to ensure packet integrity
            calculated_checksum = sum(packet[:4] + payload) & 0xFFFFFFFF
            if checksum != calculated_checksum:
                logger.warning(f"Checksum mismatch for packet {seq_num}. Dropping packet.")
                continue  # Drop the packet if checksum doesn't match

            # Store the packet if it's not already received
            if seq_num not in received_packets:
                received_packets[seq_num] = payload
            else:
                logger.warning(f"Duplicate packet {seq_num}. Dropping packet.")
                # Send acknowledgment for the duplicate packet
                ack = struct.pack('!I', seq_num)
                sock.send(ack)
                logger.info(f"Sent ACK for packet {seq_num}")
                continue  # Drop the packet if it's a duplicate

            # Write sequential packets to the destination
            while expected_seq in received_packets:
                logger.info(f"Reconstructed packet for {expected_seq}")
                # Send acknowledgment for the received packet
                ack = struct.pack('!I', expected_seq)
                sock.send(ack)
                logger.info(f"Sent ACK for packet {expected_seq}")
                # Write the payload to the destination
                dest.write(received_packets[expected_seq])
                num_bytes += len(received_packets[expected_seq])
                dest.flush()  # Ensure data is written out immediately
                # Remove the packet from the dictionary and update the expected sequence number
                del received_packets[expected_seq]
                expected_seq += 1

        except socket.timeout:
            logger.warning("Timeout occurred while waiting for a packet.")
            continue  # Continue to the next iteration on timeout

    return num_bytes

