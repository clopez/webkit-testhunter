# WebKit-TestHunter

Utilities to parse the WebKit Layout Test results history and print
the results for a given test grouped by revision intervals or detect
tests that are flaky.

Note: This tracks only the bots from the GTK and WPE ports of WebKit.
However, support for other ports should be really easy to add (open an issue
if you are interested).

The repository includes also the data from the bots that is updated daily.

However, before running wktesthunter is always a good idea to update
the json files.


# Update the json files

 * Execute: `./resync`
 * When updating if it prints warnings about not beeing able to
   fetch data for some revisions then is usually safe to ignore it.
   (probably that revisions failed to compile webkit, therefore
    there are no test results for them)


# Check history of past results for a test

* Typical usage:

  * `./wktesthunter testdir/testname.html`

* Use the `--bot` argument to select the bot you want to check.
* Check `./wktesthunter -h` for additional help.


# Detect flaky tests to be added to the TestExpectations file

* Typical usage:

  * `./flakyhunter`

* Use the `--bot` argument to select the bot you want to check.
* Use the `--webkitdir` argument to pass the path to your WebKit checkout.
  This makes the script to discard tests that modified on the interval
  checked.
* Check `./flakyhunter -h` for additional help.


# Check history of results older than a year

Due to the continous grow of files some cleaning is done from time to time,
otherwise too much disk space is wasted keeping files around that are hardly
useful.

At any moment you can expect to have available on the repo at least 1 year
worth of data history.

If you need to query data older than that you can resurrect the old results
from the git history.

The following commands will recover the history for you:

* History older than `250000@main` (From Apr 2014 to 26th Apr 2022)
  * Execute this command: ```git revert -n 4e4c323159641b2ed7004bb864f97c39c1f042d9```
  * Note: needs 30GB **more** of disk space
