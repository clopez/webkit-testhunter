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

 * Execute: `./fetch.sh` (or just git pull, there is a cronjob that does this daily
   and commits the result)
 * Is safe to ignore the warnings about revisions not available
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
