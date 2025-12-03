import os
import signal

class OptionalColorText():

    def __init__(self, usecolor=True):
        self.should_use_color = usecolor

    def bold(self, text):
        if self.should_use_color:
            return "\033[1m%s\033[0m" % text
        return text

    def green(self, text):
        if self.should_use_color:
            return "\033[0;32m%s\033[0m" % text
        return text

    def red(self, text):
        if self.should_use_color:
            return "\033[0;31m%s\033[0m" % text
        return text


def sigterm_this_process(signum, frame):
    os.kill(os.getpid(), signal.SIGTERM)


def get_percent(part, total):
    return float(100) * float(part) / float(total)


def get_percent_str(part, total):
    percent_part = get_percent(part, total)
    return "%d%%" % int(percent_part) if percent_part.is_integer() else "%.1f%%" % percent_part


def calculate_flakiness_factor(results_list):
    flakiness_factor = 0
    prev_result = results_list[0]
    for result in results_list:
        # If in a run it got two results means it was already flaky in that run
        if ' ' in result:
            flakiness_factor += 1
        elif result != prev_result:
            flakiness_factor += 1
        prev_result = result
    return get_percent(flakiness_factor, len(results_list))
