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
Parse cts-v model page and follow listings, downloading them to a cache. 
```
(py3) > python ./trend.py -u https://bringatrailer.com/cadillac/cts-v/
Downloaded https://bringatrailer.com/cadillac/cts-v/:/var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//cadillac/cts-v.html
Downloaded https://bringatrailer.com/listing/2012-cadillac-cts-v-2/:/var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//listing/2012-cadillac-cts-v-2.html
Downloaded https://bringatrailer.com/listing/2012-cadillac-cts-v-4/:/var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//listing/2012-cadillac-cts-v-4.html
....
Done: ./cts-v.csv
```
By default it waits 5 seconds before hitting the next BaT URL to be nice to their website.

Running the same command again, will read from cache instead of hitting BaT again:
```
(py3) > python ./trend.py -u https://bringatrailer.com/cadillac/cts-v/
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//cadillac/cts-v.html ...
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//listing/2012-cadillac-cts-v-2.html ...
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//listing/2012-cadillac-cts-v-4.html ...
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//listing/2011-cadillac-cts-v-5.html ...
Reading ....
Done: ./cts-v.csv
```
Don't follow listings (it will not get year, milage, and transmission information):
```
(py3) >  python ./trend.py -results-only -u https://bringatrailer.com/cadillac/cts-v 
Reading from cache /var/folders/qg/8qfb3sy12hq_jl3qhlnk43pc0000gn/T//cadillac/cts-v.html ...
Done: ./cts-v.csv
```

