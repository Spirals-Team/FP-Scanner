Repository containing the code of FP-Scanner's paper.

# Create virtual environment and install dependencies

Run the command below to create a virtual environment.
```ruby
virtualenv --python=/usr/bin/python3 myvenv
```

Then activate the virtual environment.
```ruby
. myvenv/bin/activate
```

Finally, install the dependencies.
```ruby
pip install -r requirements.txt
```

# Import database

Our prototype relies on MongoDB to store the fingerprints, thus you need to ensure that MongoDB is running.

Run the command below to import the database. 
```ruby
mongoimport --db usenix18 --collection fingerprint --file fingerprints.json 
```

# Scan fingerprints

First, we analyze the fingerprints present in the database.

```ruby
python main.py
```

It logs information on the screen about the results of the analysis and generates two csv result files in the *results* folder:
- *res_prediction.csv* that contains information on the tests that passed or not for each fingerprint;
- *res_real_values.csv* that contains information on the OS and browser predicted for each fingerprint.

Then we analyse these files to obtain the accuracy of FP-Scanner, FingerprintJS2 and Augur.

```ruby
python main.py analyse
```


# Benchmark

To run the benchmark that measures the execution time of the scanner, run the command below.
```ruby
python main.py bench
```

It generates three files *bench_situation1.csv*, *bench_situation2.csv* and *bench_situation3.csv* that corresponds to
the three cases presented in the article:
1. Run all scanner tests even when an inconsistency is detected;
2. Stop running tests when an inconsistency is detected;
3. Run only analysis of the pixels.

These files contain a single column called *elapsed_time*, which represent the execution time 
needed to run the set of tests.