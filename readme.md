# Trimiata bot

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

## Функции
* `/stock_data_equivalence` - делает запрос к 1С, получает данные о результатах сверки без предварительного запроса к сайту
* `/stock_data_equivalence_update` - делает запрос к 1С, получает данные о результатах сверки с предварительным запросом к сайту
* `/find_photos_with_same_article` - в папке `/SOURCES/PHOTO` собирает уникальные штрихкоды, подтягивает их артикулы и если есть одинаковые артикулы для разных штрихкодов, то собираются все фотографии содержащие эти штрихкоды и подготавливает отчет
* `/rename_photos`
  * подготавливается таблица файлов из папки `/SOURCES/PHOTO`
  * извлекается штрихкод из названия файла и по штрихкоду подтягиваются данные артикула из 1С
  * удаляет все фотографии в папке `/RENAMED/PHOTO`
  * производится операция копирования с переименованием из `/SOURCES/PHOTO` в `/RENAMED/PHOTO`