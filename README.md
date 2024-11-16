# Homework 5: Reliable Communication

In this homework, you will implement reliable communication over an unreliable
link, just like TCP.

You will be provided with code that simulates an unreliable link between sender
and receiver.  This link has a very constrained buffer (only two packets can
be 'in flight' at a time), and can have arbitrary delay and loss rates.  Your
job will be to create and implement a protocol over this connection that
correctly transfers data, in a reasonable amount of time.


### Writing Your Solution

This repo contains several tools that will help you simulate and test your
solution.  **You should not make changes to any file other than `hw5.py`.**
All other files contain code used to either simulate the unreliable connection,
or code to help you test your your solution.

Your solution / `hw5.py` file will be tested against stock versions of all the
other files in the repo, so any changes you make will not be present at
grading time.

Your solution must be contained in the `send` and `recv` functions in `hw5.py`.
You should not change the signatures of these functions, only their bodies.
These functions will be called by the grading script, with parameters
controlled by the grading script.  Your solution must be general, and should
work for any file.

Your task is to modify the bodies of these functions so that they communicate
using a protocol that ensures that the data sent by the `send` function
can be reliably and quickly reconstructed by the `recv` function.  You should
do so through a combination of setting timeouts on socket reads (e.x.
`socket.timeout(float)`) and developing a system through which each side can
acknowledge if / when they receive a packet.

Remember that the connection is bandwidth constrained.  No more than two
packets can be "on the wire" at a time. If you send a third packet while
there are already two packets traveling to their destination (in either
direction), the third packet will be dropped, so it is important that you get
your timeouts and your acknowledgments right.


### Testing Your Solution

You can use the provided `tester.py` script when testing your solution.  This
script uses the `receiver.py`, `sender.py`, and `server.py` scripts to
simulate an unreliable connection, and to test your solution.

The `tester.py` script contains many parameters you can use to test your
solution under different conditions, and to receive different amounts
of debugging information to better understand the network.  These
parameters and options can be viewed by calling `tester.py --help`, and are
also reproduced below.


    usage: tester.py [-h] [-p PORT] [-l LOSS] [-d DELAY] [-b BUFFER] -f FILE
                    [-r RECEIVE] [-s] [-v]

    Utility script for testing HW5 solutions under user set conditions.

    optional arguments:
    -h, --help            show this help message and exit
    -p PORT, --port PORT  The port to simulate the lossy wire on (defaults to
                            9999).
    -l LOSS, --loss LOSS  The percentage of packets to drop.
    -d DELAY, --delay DELAY
                            The number of seconds, as a float, to wait before
                            forwarding a packet on.
    -b BUFFER, --buffer BUFFER
                            The size of the buffer to simulate.
    -f FILE, --file FILE  The file to send over the wire.
    -r RECEIVE, --receive RECEIVE
                            The path to write the received file to. If not
                            provided, the results will be written to a temp file.
    -s, --summary         Print a one line summary of whether the transaction
                            was successful, instead of a more verbose description
                            of the result.
    -v, --verbose         Enable extra verbose mode.


For example, to see how your solution performs when transmitting a text file,
with a 20% loss rate, and with a latency of 100ms, you could use the following:
`python3 tester.py --file test_data.txt --loss 0.2 --delay 0.1`. Make sure to
run this program multiple times in order to confirm correctness of your code.


### Hints and Suggestions

 * A key part of this homework is determining how long to wait before resending
   a packet.  You should estimate this timeout value using the EWMA technique
   for estimating the RTT, and use this in determining your timeout. With
   correctly tuned timeouts, lower RTT will result in higher throughput.

   A good way of determining the timeout to use is the "estimated RTT +
   (deviation  of RTT * 4)".  You should check with your book for more details.

 * Use the included `--verbose` option to include very detailed information
   about what your code is sending over the network, and how the network
   is handling that data.

 * Use the included `--receive` option to see the results of your file transfer.
   By default, the testing script will store the results of your code to a
   temporary location.  This option may be useful if you're not sure how or
   why the received file does not match the sent file.

 * Make sure you try your solution under many different loss ratios and
   latencies by changing the parameters in the `tester.py` script.

 * Keep your packets smaller than or equal to `homework5.MAX_PACKET` (1400
   bytes).

 * Pay attention to the end of the connection. Ensure that both sides of the
   connection finish without user assistance, even if packet losses occur,
   while guaranteeing that the entire file is transferred. Look at the
   FIN/FINACK/ACK sequence in TCP for ideas.


### Grading

You solution will be graded by using it to transfer five different files,
each under different simulated test conditions.  For each test case, there is a
minimum throughput requirement and a timeout for your program to exit.
The timeout is set as 50% more than the corresponding required throughput.

Each test case will be scored accordingly:

| Case                                           | Points Earned  |
| ---------------------------------------------- | -------------  |
| File is not transmitted correctly              |             0  |
| Transmission takes longer than the max time    |             0  |
| Successful transmission, but low throughput    |             10 |
| Successful transmission, fast throughput       |             20 |


If your program exits normally before the timeout, but the content of the
received file is invalid, then **zero points** are awarded.

If your program doesn’t exit before the timeout, it will be terminated
before completion, resulting in incorrect file content, and so **0 points**.

If the program exits normally before the timeout and the received file’s content
is valid *but* the throughput obtained is lower than the required minimum
throughput then you receive **10 point**.

If your program correctly transmits the file below the timeout, and with the
required throughput, it will receive **20 points**.

* Do not change arguments of the functions in `hw5.py`. You will be making changes to `hw5.py` only.



