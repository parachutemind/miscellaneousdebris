# miscellaneousdebris
A mix bag of scripts and tools

## scripts/bat
#### trend.py
Export BaT model page and associated listing information into a CSV and generate various charts

- Install (requires Python >= 3)
```
> git clone git@github.com:parachutemind/miscellaneousdebris.git
> cd miscellaneousdebris/scripts/bat
> pip install -r requirements.txt 
```

- Usage:  
```
python ./trend.py -h
```

E.g.,
```
(py3) > python ./trend.py -u https://bringatrailer.com/cadillac/cts-v/
Downloaded https://bringatrailer.com/cadillac/cts-v/
Done: ./cts-v.csv
```
Running the same command again, will read from cache instead of hitting BaT again:
```
(py3) > python ./trend.py -u https://bringatrailer.com/cadillac/cts-v/
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T/cts-v.html ...
Done: ./cts-v.csv
```
Don't follow listings (it will not get year, milage, and transmission information):
```
(py3) >  python ./trend.py -dont-follow -u https://bringatrailer.com/cadillac/cts-v 
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//cadillac/cts-v.html ...
Done: ./cts-v.csv
```

