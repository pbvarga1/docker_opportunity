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

* [Docker](https://docs.docker.com/)
    * Testing with Docker: Creating a temporary database in docker and using
      the database to test as if on a live server
* [PostgreSQL](https://www.postgresql.org/docs/)
* [Flask](http://flask.pocoo.org/)
    * [Blueprints](http://flask.pocoo.org/docs/1.0/blueprints/)
* [Flask-SQLAlchemy](http://flask-sqlalchemy.pocoo.org/2.3/)
* [REST API](https://en.wikipedia.org/wiki/Representational_state_transfer)
* [Angularjs](https://docs.angularjs.org/api)
    * [angular-ui bootstrap modals](https://angular-ui.github.io/bootstrap/#!#modal)
    * [components](https://docs.angularjs.org/guide/component)
    * [routing](https://docs.angularjs.org/tutorial/step_09)
    * [services](https://docs.angularjs.org/api/ng/type/angular.Module#service)
* Flask + Angular
    * Routing to multiple pages handled by Angular through Flask
* [pytest](https://docs.pytest.org/en/latest/contents.html)
    * [fixtures](https://docs.pytest.org/en/latest/fixture.html)
* [mock](https://docs.python.org/3/library/unittest.mock.html)
* [Travis-CI](https://docs.travis-ci.com/)
* [coveralls (code coverage)](https://docs.coveralls.io/)
* [flake8 (pep8 style guide)](http://flake8.pycqa.org/en/latest/)
* [python packaging](https://packaging.python.org/tutorials/packaging-projects/#creating-setup-py)
* [yarn](https://yarnpkg.com/en/)
    * js package management in general
