#!/bin/sh

sh get_news_url.sh &
sh get_news_content.sh &
sh get_news_view.sh &
sh get_disk_usage.sh
