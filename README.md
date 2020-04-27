# Local dev

## Environment Setup
Install docker and docker-compose

Set up environment variables
```bash
cp .env.example .env
```

Start the server

```bash
docker-compose up -d
```

Run database migrations

```bash
docker-compose run --rm app alembic upgrade head
```

Test to make sure everything is working

```bash
curl localhost:8000/webhook/record_trade_volume
```

Should return:

```json
{
  "success": true
}
```

## Running unit tests

```bash
dc run --rm app pytest app/tests
```

## Typechecking
```bash
dc run --rm app mypy app
```

## Format code
```bash
dc run --rm app black app
```

# Updating trade volumes in local dev

```bash
dc run --rm app python -m app.update_trade_volumes
```

# Deploy with heroku

Install heroku cli and log in

From the project directory:
```bash
heroku create
heroku stack:set container
heroku addons:create heroku-postgresql:hobby-dev
# Since we make one database connection per worker and
# the hobby-dev postgres plan has a limited number of connections
# we set the number of workers very low to avoid hitting the cap
heroku config:set WEB_CONCURRENCY=2
heroku config:set SENDGRID_API_KEY=<sendgrid_api_key>
heroku config:set USE_REAL_MAILER=true
heroku config:set NOTIFY_EMAILS=one@example.com,two@example.com
# Deploy
git push heroku master
# Run database migrations
heroku run poetry run alembic upgrade head
# Open the app
heroku open
```
Then navigate to /docs on the opened page

# Set up regular updates
```bash
heroku addons:create scheduler:standard
heroku addons:open scheduler # will open a browser tab
```

There's no CLI interface to set up a schedule unfortunately

enter `python -m app.update_trade_volumes.py` in the run command box and pick your desired update frequency

# Thoughts on future

## Scalability

### Tracking many metrics

Currently we load all tracked metrics in memory in a single process, if the number of tracked metrics is very large that
may no longer be feasible. We could instead request the metrics and store them to the database in batches. We would
have to also move the ranking process into a system that can write to a filesystem (e.g. the database).

If fetching all of the metrics takes too long, we can split the work into batches of metrics and run them in parallel,
but that would require coordinating across those parallel workers to track when they are all done so the ranking can be
calculated

### Sampling metrics frequently

Sampling metrics frequently will result in a large amount of data stored. Since the only use for the historical data in
this API is to display a graph of a 24 hour period, we can figure out the minimum number of data points required to make
a nice-looking graph and coalesce older metric values by taking an average of the data over a period of time. We can
also of course drop records older than 24 hours. If we want to keep the historical data, we can instead move it to a
historical table to keep the hot table relatively small or export it to another datastore for colder storage.

Sampling metrics frequently will also benefit from splitting out the email processing into its own background task as
described in the handling many users section as it will reduce the run time of the ingest job

### Handling many users

To improve latency and throughput on the volume_history API we could move the history fetching and rank calculation to
ingest time and store them in a memory-only store like redis or memcached. Then, instead of fetching from the database
and recalculating ranks on each API call, volume_history would just load the data from the memory-only store and return
it. With this model we can scale with many redis/memcache read-replicas since the traffic will be extremely read-heavy.

Another consideration with many users is it may take too long to send alert emails to all of the users during the ingest
process. Instead of doing that inline we can trigger another background process to do the alert analysis and email
process after ingest so that the email sending process doesn't block the ingest from finishing

## Monitoring

There are two portions of the application that should be monitored, the REST API and the ingest process.

Any off-the-shelf APM monitoring solution should track the API without much additional work, but the key metrics to track
there are response status codes and percentile latencies. It's also a good idea to alert on sudden drops in traffic if
traffic is regular enough to support that, and set up an external service to do a basic sanity check by calling the API
regularly and reporting failures.

For the ingest process we should track run time, exit codes, and the last successful run time. If the run time gets too
long, there's a non-successful exit code, or the last successful run was too long ago, we should alert. Most (all?)
APM/monitoring solutions support custom metrics, so we can have the ingest process report runtime (or if the scheduling
system we use tracks that information externally we can query it from their API). We can regularly fetch last ingest
time from the database to expose that to the monitoring solution for alerting. We should also track how many metrics
are updated in each sync, or fail the job if not all metrics are synced to expose issues with partial data fetching

## Testing

For a production application we would need much better unit test coverage to feel confident about releasing frequently.
The most valuable unit test coverage would be getting better branch coverage on `CurrencyTradeVolumeService`, including
covering more unlikely scenarios like being unable to find the average volume for a currency pair and coverage for
`LivecoinApi` covering scenarios like the API being down, returning unexpected data, timing out, etc... It would also be
useful to pull a real JSON response from the Livecoin API to use in testing `LivecoinApi`

I would also like integration tests to verify `CurrencyTradeVolumeStore` can successfully and correctly fetch data from
the database and the whole api -> service -> database and cli -> api -> database processes function successfully.

# Limitations

The deployed application uses the free heroku scheduler to schedule the ingestion job, which is designed only to run
short jobs, and cannot be scheduled to run more frequently than every ten minutes. A real deployment would have to use a
more robust job scheduler.

It also uses the free heroku postgres addon, which can only contain 10k rows, so I've drastically reduced the number of
metrics it tracks to allow it to keep a couple days worth of data. For the deployment to survive longer-term we will
need to schedule a job to automatically clean up old data.
