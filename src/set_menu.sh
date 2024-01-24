curl -XGET "https://api.telegram.org/bot$TELEGRAM_TOKEN/deleteMyCommands"
curl -XGET -H "Content-type: application/json" -d "$(cat menu_ru.json)" "https://api.telegram.org/bot$TELEGRAM_TOKEN/setMyCommands"
exit
