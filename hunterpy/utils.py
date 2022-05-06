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
