Faster versions of libraries: cchardet, pydantic compiled
Exponential backoff for livecoin api
Doing a background task in the context of an http request makes me nervous
improve perf by doing the query at ingestion time, sticking the result in redis
Can clear the old one at injestion time so there's no data staleness issue

# Environment setup

Install docker and docker-compose

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
