Faster versions of libraries: cchardet, pydantic compiled
Exponential backoff for livecoin api
Doing a background task in the context of an http request makes me nervous
improve perf by doing the query at ingestion time, sticking the result in redis
Can clear the old one at injestion time so there's no data staleness issue

# Local dev

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
