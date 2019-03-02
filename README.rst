Opportunity App
===============

.. image:: https://travis-ci.com/pbvarga1/opportunity.svg?branch=master
    :target: https://travis-ci.com/pbvarga1/opportunity
.. image:: https://coveralls.io/repos/github/pbvarga1/opportunity/badge.svg?branch=master
    :target: https://coveralls.io/github/pbvarga1/opportunity?branch=master


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


Software
--------

Software/techniques/packages used so far.

* `Docker <https://docs.docker.com/>`_

    * Testing with Docker: Creating a temporary database in docker and using
      the database to test as if on a live server; Creating a redis server and
      testing against that.
    * `Multistage build <https://docs.docker.com/develop/develop-images/multistage-build/>`_

* `PostgreSQL <https://www.postgresql.org/docs/>`_
* `Flask <http://flask.pocoo.org/>`_

    * `Blueprints <http://flask.pocoo.org/docs/1.0/blueprints/>`_

* `Flask-SQLAlchemy <http://flask-sqlalchemy.pocoo.org/2.3/>`_
* `REST API <https://en.wikipedia.org/wiki/Representational_state_transfer>`_
* `Angularjs <https://docs.angularjs.org/api>`_

    * `angular-ui bootstrap modals <https://angular-ui.github.io/bootstrap/#!#modal>`_
    * `components <https://docs.angularjs.org/guide/component>`_
    * `routing <https://docs.angularjs.org/tutorial/step_09>`_
    * `services <https://docs.angularjs.org/api/ng/type/angular.Module#service>`_

* Flask + Angular

    * Routing to multiple pages handled by Angular through Flask

* `pytest <https://docs.pytest.org/en/latest/contents.html>`_

    * `fixtures <https://docs.pytest.org/en/latest/fixture.html>`_

* `mock <https://docs.python.org/3/library/unittest.mock.html>`_
* `Travis-CI <https://docs.travis-ci.com/>`_
* `coveralls (code coverage) <https://docs.coveralls.io/>`_
* `flake8 (pep8 style guide) <http://flake8.pycqa.org/en/latest/>`_
* `python packaging <https://packaging.python.org/tutorials/packaging-projects/#creating-setup-py>`_
* `yarn <https://yarnpkg.com/en/>`_

    * js package management in general

* `redis <https://redis.io/>`_

    * `redis-py <https://redis-py.readthedocs.io/en/latest/>`_
    * `redis hashes <https://redis.io/topics/data-types#hashes>`_

* `Type Hints <https://www.python.org/dev/peps/pep-0484/>`_

    * `Python typing <https://docs.python.org/3.6/library/typing.html>`_
    * `Static Type Checking with Mypy <https://www.python.org/dev/peps/pep-0484/>`_
    * `Stub Files <https://www.python.org/dev/peps/pep-0484/#stub-files>`_

        * See also `Mypy Stubs <https://mypy.readthedocs.io/en/latest/stubs.html>`_

* `Swagger <https://swagger.io/>`_

    * `OpenAPI 3.0 <https://swagger.io/docs/specification/about/>`_
    * `OpenAPI 2.0 <https://swagger.io/docs/specification/2-0/basic-structure/>`_

        * `See this commit <https://github.com/pbvarga1/opportunity/blob/
          d4f523093d41a288096a04656560397e9d6ac690/app/swagger.json>`_

* `Sphinx Documentation <http://www.sphinx-doc.org/en/master/>`_

    * `Restructured Text (rst) format <http://www.sphinx-doc.org/en/master/
       usage/restructuredtext/basics.html>`_
    * `Autodoc extension <http://www.sphinx-doc.org/en/master/usage/
       extensions/autodoc.html>`_
    * `NumpyDoc extension <https://numpydoc.readthedocs.io/en/latest/
       install.html#sphinx-config-options>`_

* `Numpy Docstrings <https://numpydoc.readthedocs.io/en/latest/format.html>`_


Quick Start
-----------

If you want to use this project for your own learning exercises, fork the repo
to your own github account and then clone your forked repo to your computer.
Make sure docker is installed and running. If you are **not** using docker
toolbox, set the following environment envariable:

```shell
$ export DOCKER_IP='127.0.0.1'
```

 From the top directory ``oportunity``, run:

```shell
$ docker-compose up
```

Which will build the images and run the docker containers. If you are using
dockertoolbox, then the host will be ``192.168.99.100``, otherwise it will be
the local host ``127.0.0.1``. In the examples ahead, I assume the host will
be ``127.0.0.1``. In your browser go to ``http://127.0.0.1:5002/`` to
see the home web page:

.. image:: homepage.jpg

The first two links allow you to register product types (i.e. EDR, RDR) and
cameras (i.e. pancam). The third link is where you will find images to
register. Clicking ``Register Image`` allows you to register an image with the
local database and then select it for viewing. Selecting an image will display
it on the home page.

Port ``5001`` is where the API is located to retrieve data from the database.

Links
-----

+----------------+-----------------------------+------------------------+
|   Page         |      Toolbox                |     Docker             |
+================+=============================+========================+
|   **Home**     | http://192.168.99.100:5002/ | http://127.0.0.1:5002/ |
+----------------+-----------------------------+------------------------+
|   **Docs**     | http://192.168.99.100:5005/ | http://127.0.0.1:5005/ |
+----------------+-----------------------------+------------------------+
|   **Swagger**  | http://192.168.99.100:5004/ | http://127.0.0.1:5004/ |
+----------------+-----------------------------+------------------------+
