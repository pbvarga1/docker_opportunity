# Opportunity App

[![Build Status](https://travis-ci.com/pbvarga1/docker_opportunity.svg?branch=master)](https://travis-ci.com/pbvarga1/docker_opportunity)
[![Coverage Status](https://coveralls.io/repos/github/pbvarga1/docker_opportunity/badge.svg?branch=master)](https://coveralls.io/github/pbvarga1/docker_opportunity?branch=master)

I want to play around with some programming techniques (listed below). This
repo can be used as examples of using these techniques (although I do not
guarantee that they are all the *best* way to do things as I am just learning).
To explore these techniques, I'm creating a simple app and adding just enough
complexity to serve as real world examples without it becoming too large. The
application is a local website where one can look at images taken by the
opportunity rover. This website will have a PostgreSQL database which is
managed by Flask-SQLAlchemy. The front-end will be run by flask. These services
are extracted into different applications called ``app`` and ``web``. See the
issues for what I plan to do going forward.


## Software

Software/techniques/packages used so far.

* Docker
    * Testing with Docker
* PostgreSQL
* Flask
* Flask-SQLAlchemy
* REST API
* Angularjs
* pytest
