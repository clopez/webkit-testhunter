# Plotting test data

## Software needed

* Python3
* Pandas
* Matplotlib

## Generating the csv with test data

```
<wktesthunter>/charts/report.py jsonresults/WPE-Linux-64-bit-Release-Tests/full_results_r2* -o wpe-release.csv
```

## Plotting the data

```
<wktesthunter>/charts/plot.py <csv generated by report.py>
```

It'll generate two charts. One for the number of passing, skipped, and gardened
tests and another for the regressions and flakies.

## TODO

Some plotting options are hardcoded in the scripts

* [ ] Customize the data ranges
* [ ] Generated image size
* [ ] Legend box position