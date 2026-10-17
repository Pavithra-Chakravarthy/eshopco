# eShopCo Config API

## Local run (PowerShell)

```powershell
python -m pip install -r requirements.txt
$env:APP_PORT = "8835"
$env:APP_DEBUG = "true"
$env:APP_API_KEY = "key-bm4ojea4u0"
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://127.0.0.1:8000/effective-config`.

Test overrides:
`http://127.0.0.1:8000/effective-config?set=port=9000&set=debug=true`

## Deployment

Deploy this folder as a Python web service on a host such as Render. Use build command:

`pip install -r requirements.txt`

Use start command:

`uvicorn main:app --host 0.0.0.0 --port $PORT`

Set these deployment environment variables:
- `APP_PORT=8835`
- `APP_DEBUG=true`
- `APP_API_KEY=key-bm4ojea4u0`
- `APP_ENV=development`

Do not set `APP_WORKERS` unless you want it to override `.env`'s `NUM_WORKERS=1`.

After deployment, test:
`https://YOUR-SERVICE-HOST/effective-config?set=port=9000&set=debug=true`

Expected relevant values for that test: `port` is `9000`, `debug` is `true`, `workers` is `1`, and `api_key` is always `****`.
