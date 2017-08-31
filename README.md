# WebKit-TestHunter
Small utiliy to parse the WebKit Layout Test results history and print
all the results for a given test grouped by revision intervals.

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


# Hunt the results of a test

* Typical usage:

  * `./wktesthunter testdir/testname.html`

* Use the `--bot` argument to select the bot you want to check.
* Check `./wktesthunter -h` for additional help.
* Note: This runs faster with python3. (will use it by default if is installed)
