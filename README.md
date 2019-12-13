# miscellaneousdebris
A mix bag of scripts and tools

#### scripts/bat
Given a BaT car category text or the full URL to such category, sort it by sold/not sold price and generate a CSV file.

- Install (requires Python >= 3)
```
> git clone git@github.com:parachutemind/miscellaneousdebris.git
> cd miscellaneousdebris/scripts/bat
> pip install -r requirements.txt 
```

- Usage:  
`usage: trend.py [-h] (-f FOLDER | -u URL) [-o OUTPUT_FILE]`

E.g.,
```
(py3) python ./trend.py -u https://bringatrailer.com/cadillac/cts-v/
Downloaded https://bringatrailer.com/cadillac/cts-v/
Done: ./cts-v.csv
```
Running the same command again, will read from cache instead of hitting BaT again:
```
> python ./trend.py -u https://bringatrailer.com/cadillac/cts-v/
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T/cts-v.html ...
Done: ./cts-v.csv

```


