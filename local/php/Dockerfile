FROM php:8.3-apache
RUN apt-get update && apt-get install -y --no-install-recommends libpq-dev libonig-dev \
 && rm -rf /var/lib/apt/lists/* \
 && docker-php-ext-install pdo pdo_pgsql mbstring \
 && a2enmod rewrite headers \
 && echo "date.timezone=Asia/Bangkok" > /usr/local/etc/php/conf.d/tz.ini
WORKDIR /var/www/html
