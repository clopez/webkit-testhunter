NOERROR="NOERROR"
UNKNOWN="UNKNOWN"

bots = { # The reason to have more than one entry per bot is that some bots where renamed along the history.
    'gtk-release' : ["GTK-Linux-64-bit-Release", "GTK-Linux-64-bit-Release-WK2-Tests", "GTK-Linux-64-bit-Release-Tests"],
    'gtk-debug' : ["GTK-Linux-64-bit-Debug-Tests"],
    'wpe-release' : ["WPE-Linux-64-bit-Release-Tests"],
    'wpe-debug' : ["WPE-Linux-64-bit-Debug-Tests"],
    'wpe-arm64-release' : ["WPE-Linux-ARM64-bit-Release-Tests"]
}

# Revision namespace per bot.
#
# The trunk bots identify each build with a plain "<N>@main" identifier and we
# use <N> directly as the (monotonic) revision number.
#
# Bots that track a WebKit stable branch use a different namespace: their build
# identifier looks like "<base>.<seq>@<branch>/<version>" (for example
# "305877.970@webkitglib/2.52"). On such a branch <base> and <version> are
# constant (the branch point and the release series) and only <seq> increments,
# so we use <seq> as the monotonic revision number and reconstruct the full
# identifier for display and for git lookups.
_DEFAULT_BRANCH_INFO = {'branch': 'main', 'base': None, 'version': None, 'nested_build_dir': False}

bot_revision_info = {
}


def get_bot_revision_info(bot_key):
    return bot_revision_info.get(bot_key, _DEFAULT_BRANCH_INFO)


def is_branch_bot(bot_key):
    return get_bot_revision_info(bot_key)['branch'] != 'main'


def revision_seq_from_id(rev_id):
    # rev_id is the revision part of an identifier, e.g. "257598@main" (trunk)
    # or "305877.970@webkitglib" (stable branch). Returns the monotonic integer
    # revision number: the plain number for trunk, the branch sequence otherwise.
    core = rev_id.split('@')[0]
    if '.' in core:
        return int(core.split('.')[-1])
    return int(core)


def revision_seq_from_filename(filename):
    # filename like "full_results_257598@main_b4216.json" or
    # "full_results_305877.970@webkitglib_b39.json".
    rev_id = filename.split("full_results_")[1].split(".json")[0].split('_')[0]
    return revision_seq_from_id(rev_id)


def format_revision(seq, bot_key):
    info = get_bot_revision_info(bot_key)
    if info['base'] is None:
        return "%d@%s" % (seq, info['branch'])
    return "%d.%d@%s" % (info['base'], seq, info['branch'])


def format_interval(start, end, bot_key):
    return "[%s-%s]" % (format_revision(start, bot_key), format_revision(end, bot_key))
