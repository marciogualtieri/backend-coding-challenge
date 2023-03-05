# TODO

> Can we use a database? What for? SQL or NoSQL?

Given that the application depends on an external API, we could use a database to cache responses from the GitHub API.
That could increase performance considerably.

Refering to the GitHub API's [documentation](https://docs.github.com/en/rest/gists/gists?apiVersion=2022-11-28#list-public-gists), listing
public gists supports the query parameter `since` (a date in ISO 8601 format) that only show gists updated from a particular date.

We could save the last date a gist for a particular user was fetched from the API and on the next call only retrieve gists updated since that date.

That could improve performance considerably since we would not be required to retrieve all gists all over again. Perhaps not at all, simply returning the last cached response.

The data models (Gists, and corresponding gist files, each one with a correspondent unique key) are pretty simple, thus, a relational database seems unnecessary given the current requirements. For the purpose of caching GitHub API's data, a key-value database (NonSQL) could certainly be used with better performance.

Another use for a database would be user authentication for greater safety and protect against abuses.

> How can we protect the api from abusing it?

Per GitHub API's documentation, it [already imposes rate limits](https://docs.github.com/en/rest/overview/resources-in-the-rest-api?apiVersion=2022-11-28#rate-limiting).

However, would make sense that the application imposes its own rate limits. A database and user authentication would be useful for this purpose.


> How can we deploy the application in a cloud environment?

There are several ways to do that:

1. We could write [Helm](https://helm.sh/docs/topics/charts/) charts and use the included [Dockerfile](./Dockerfile) to deploy the app to any Kuberntes cluster in the cloud (AWS, GCP, Azure). In my opinion, that's the best option, given that it makes it cloud provider independent.

The include Dockerfile, uses [Gunicorn](https://gunicorn.org/) as the WSGI HTTP server.

2. We could deploy the application using a Python package such as [Zappa](https://github.com/zappa/Zappa). The only caveat here is that Zappa only supports AWS to my knowledge.

3. Being web frameworks such as Flask and Django quite obiquitous, all major cloud providers provide guidelines and tools to these two
in their corresponding cloud environments (AWS, GCP, Azure, Heroku).


> How can we be sure the application is alive and works as expected when deployed into a cloud environment?

We could implement a health-check route on our Flask application for this purpose, where we check for some conditions that guarantee the application is alive and in working order, e.g.: Database connection can be stablished, connection with the GitHub API can be stablished, etc.

Functional testing, in my opinion, should be done in automated tests, e.g., integration and end-to-end tests during CI/CD.

> Any other topics you may find interesting and/or important to cover

1. The original version of `gists_for_user()` wasn't written to handle GitHub API's pagination, thus, given that the default `per_page` is 30, it would only allow search in the first 30 gists for a particular user. This function has been modified to handle pagination.

2. Regarding the handling of large gists, that is, with a large number of files, I opted for using [aiohttp](https://docs.aiohttp.org/en/stable/) and (asyncio)[https://docs.python.org/3/library/asyncio.html]. Given that our application is I/O bound, that should increase performance considerably when comparing with simply using [requests](https://requests.readthedocs.io/en/latest/).

3. There's no POST data validation in the search end-point, thus, I decided to use [flask-expects-json](https://pypi.org/project/flask-expects-json/) for this purpose.

4. Please refer to [GUIDE.md](./GUIDE.md) for instructions on how to create a development environment, run tests, format/lint the code, etc.
