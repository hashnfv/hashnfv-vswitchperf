# Copyright 2015 Intel Corporation.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Dummy traffic generator, designed for user intput.

Provides a model for the Dummy traffic generator - a psuedo "traffic
generator" that doesn't actually generate any traffic. Instead the
user is required to send traffic using their own choice of traffic
generator *outside of the framework*. The Dummy traffic generator
then returns the results - manually entered by the user - as its
own.
"""

import json

from tools.pkt_gen import trafficgen
from core.results.results_constants import ResultsConstants

def _get_user_traffic_stat(stat_type):
    """
    Request user input for traffic.

    :param stat_type: Name of statistic required from user

    :returns: Value of stat provided by user
    """
    true_vals = ('yes', 'y', 'ye', None)
    false_vals = ('no', 'n')

    while True:
        result = input('What was the result for \'%s\'? ' % stat_type)

        try:
            result = int(result)
        except ValueError:
            print('That was not a valid integer result. Try again.')
            continue

        while True:
            choice = input('Is \'%d\' correct? ' % result).lower()
            if not choice or choice in true_vals:
                return result
            elif choice and choice in false_vals:
                break
            else:
                print('Please respond with \'yes\' or \'no\' ', end='')


def get_user_traffic(traffic_type, traffic_conf, flow_conf, traffic_stats):
    """
    Request user input for traffic.

    :param traffic_type: Name of traffic type.
    :param traffic_conf: Configuration of traffic to be sent.
    :param traffic_conf: Configuration of flow to be sent.
    :param traffic_stats: Required output statistics (i.e. what's needed)

    :returns: List of stats corresponding to those in traffic_stats
    """
    results = []

    print('Please send \'%s\' traffic with the following stream config:\n%s\n'
          'and the following flow config:\n%s'
          % (traffic_type, traffic_conf, json.dumps(flow_conf, indent=4)))

    for stat in traffic_stats:
        results.append(_get_user_traffic_stat(stat))

    return results


class Dummy(trafficgen.ITrafficGenerator):
    """
    A dummy traffic generator whose data is generated by the user.

    This traffic generator is useful when a user does not wish to write
    a wrapper for a given type of traffic generator. By using this
    "traffic generator", the user is asked to send traffic when
    required and enter the results manually. The user controls the
    real traffic generator and is responsible for ensuring the flows
    are setup correctly.
    """
    def connect(self):
        """
        Do nothing.
        """
        return self

    def disconnect(self):
        """
        Do nothing.
        """
        pass

    def send_burst_traffic(self, traffic=None, numpkts=100, time=20, framerate=100):
        """
        Send a burst of traffic.
        """
        traffic_ = self.traffic_defaults.copy()
        result = {}

        if traffic:
            traffic_ = trafficgen.merge_spec(traffic_, traffic)

        results = get_user_traffic(
            'burst',
            '%dpkts, %dmS' % (numpkts, time),
            traffic_,
            ('frames rx', 'payload errors', 'sequence errors'))

        # builds results by using user-supplied values where possible
        # and guessing remainder using available info
        result[ResultsConstants.TX_FRAMES] = numpkts
        result[ResultsConstants.RX_FRAMES] = results[0]
        result[ResultsConstants.TX_BYTES] = traffic_['l2']['framesize'] \
                                            * numpkts
        result[ResultsConstants.RX_BYTES] = traffic_['l2']['framesize'] \
                                            * results[0]
        result[ResultsConstants.PAYLOAD_ERR] = results[1]
        result[ResultsConstants.SEQ_ERR] = results[2]

        return trafficgen.BurstResult(*results)

    def send_cont_traffic(self, traffic=None, time=20, framerate=0,
                          multistream=False):
        """
        Send a continuous flow of traffic.
        """
        traffic_ = self.traffic_defaults.copy()
        result = {}

        if traffic:
            traffic_ = trafficgen.merge_spec(traffic_, traffic)

        results = get_user_traffic(
            'continuous',
            '%dmS, %dmpps, multistream %s' % (time, framerate,
                                              multistream), traffic_,
            ('frames tx', 'frames rx', 'min latency', 'max latency',
             'avg latency'))

        framesize = traffic_['l2']['framesize']

        # builds results by using user-supplied values where possible
        # and guessing remainder using available info
        result[ResultsConstants.THROUGHPUT_TX_FPS] = float(results[0]) / time
        result[ResultsConstants.THROUGHPUT_RX_FPS] = float(results[1]) / time
        result[ResultsConstants.THROUGHPUT_TX_MBPS] = (float(results[0]) \
                                                      * framesize) / time
        result[ResultsConstants.THROUGHPUT_RX_MBPS] = (float(results[1]) \
                                                      * framesize) / time
        result[ResultsConstants.THROUGHPUT_TX_PERCENT] = 0.0
        result[ResultsConstants.THROUGHPUT_RX_PERCENT] = 0.0
        result[ResultsConstants.MIN_LATENCY_NS] = float(results[2])
        result[ResultsConstants.MAX_LATENCY_NS] = float(results[3])
        result[ResultsConstants.AVG_LATENCY_NS] = float(results[4])

        return result

    def send_rfc2544_throughput(self, traffic=None, trials=3, duration=20,
                                lossrate=0.0, multistream=False):
        """
        Send traffic per RFC2544 throughput test specifications.
        """
        traffic_ = self.traffic_defaults.copy()
        result = {}

        if traffic:
            traffic_ = trafficgen.merge_spec(traffic_, traffic)

        results = get_user_traffic(
            'throughput',
            '%d trials, %d seconds iterations, %f packet loss, multistream '
            '%s' % (trials, duration, lossrate,
                    'enabled' if multistream else 'disabled'),
            traffic_,
            ('frames tx', 'frames rx', 'min latency', 'max latency',
             'avg latency'))

        framesize = traffic_['l2']['framesize']

        # builds results by using user-supplied values where possible
        # and guessing remainder using available info
        result[ResultsConstants.THROUGHPUT_TX_FPS] = float(results[0]) \
                                                     / duration
        result[ResultsConstants.THROUGHPUT_RX_FPS] = float(results[1]) \
                                                     / duration
        result[ResultsConstants.THROUGHPUT_TX_MBPS] = (float(results[0]) \
                                                      * framesize) / duration
        result[ResultsConstants.THROUGHPUT_RX_MBPS] = (float(results[1]) \
                                                      * framesize) / duration
        result[ResultsConstants.THROUGHPUT_TX_PERCENT] = 0.0
        result[ResultsConstants.THROUGHPUT_RX_PERCENT] = 0.0
        result[ResultsConstants.MIN_LATENCY_NS] = float(results[2])
        result[ResultsConstants.MAX_LATENCY_NS] = float(results[3])
        result[ResultsConstants.AVG_LATENCY_NS] = float(results[4])

        return result

if __name__ == '__main__':
    TRAFFIC = {
        'l3': {
            'proto': 'tcp',
            'srcip': '1.1.1.1',
            'dstip': '90.90.90.90',
        },
    }

    with Dummy() as dev:
        print(dev.send_burst_traffic(traffic=TRAFFIC))
        print(dev.send_cont_traffic(traffic=TRAFFIC))
        print(dev.send_rfc(traffic=TRAFFIC))