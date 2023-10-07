# Trimiata bot

## funcs
* Предоставляет информацию по сверке с сайтом

## env vars
* `TELEGRAM_TOKEN`
* `STOCK_DATA_EQUIVALENCE`
* `1C_LOGIN`
* `1C_PASSWORD`
* `PHOTO_SOURCES_PATH`
* `PHOTO_RENAMING_URL`

## docker
* `docker build -t trim_bot:0 .`
* `docker run -d --name trim_bot --restart=always --env-file .env -v /mnt/PHOTO_SOURCES:/mnt/PHOTO_SOURCES trim_bot:0`
