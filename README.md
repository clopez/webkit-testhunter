# WebKit-TestHunter
Small utiliy to parse the WebKit Layout Test results history and print
all the results for a given test grouped by revision intervals.

Note: This only tracks the GTK release bot. But, support for other
platforms/bots should be easy to add.

The repository includes also the (GTK) json files prefetched for
a quicker start.


However, before running wktesthunter is always a good idea to update
the json files.

# Update the json files

 * Execute: `./fetch.sh`
 * Is safe to ignore the warnings about revisions not available
   (probably that revisions failed to compile webkit, therefore
    there are no test results for them)


# Hunt the results of a test

* Typical usage:

  * `./wktesthunter testdir/testname.html`

* Check `./wktesthunter -h` for additional help.
* Note: This runs faster with python3. (will use it by default if is installed)
