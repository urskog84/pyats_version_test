# PyATS Tests

My first attempt to test create a Network atuomation tests with PyATS and Genie


## How to get started
- git clone https://github.com/urskog84/pyats_version_test.git
- cd pyats_version_test
- edit /tests/testbed.yml to your need



## Run the tests with docker 

```
# Interactive 

docker run --rm -it -p 8080:8080 -v ${pwd}:/pyats_local $(docker build . -q)
``` 
``` 
# Silet

docker run --rm -p 8080:8080 -v ${pwd}:/pyats_local $(docker build . -q)
``` 

## After the are finish
you can access the html report @ http://localhost:8080

Or you can use your imagination :brain: and publish the static html file at the interweb :spider_web: