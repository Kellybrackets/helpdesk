#!/usr/bin/env bash
set -euo pipefail
source /workspace/docker/versions.env
BENCH=/home/frappe/frappe-bench
cd "$BENCH"

if [ ! -f .bench-ready ]; then
    if [ ! -d apps/frappe ]; then
        if [ ! -d /tmp/frappe-source/.git ]; then
            git clone --depth 1 --branch version-15 https://github.com/frappe/frappe.git /tmp/frappe-source
        fi
        git -C /tmp/frappe-source fetch --depth 1 origin "$FRAPPE_REVISION"
        git -C /tmp/frappe-source reset --hard "$FRAPPE_REVISION"
        bench init --ignore-exist --skip-assets --skip-redis-config-generation \
            --frappe-path /tmp/frappe-source --frappe-branch version-15 "$BENCH"
        touch .framework-ready
    fi
    if [ ! -f .framework-ready ]; then
        bench pip install -e apps/frappe
        yarn --cwd apps/frappe install --frozen-lockfile
        touch sites/apps.txt
        grep -qxF frappe sites/apps.txt || echo frappe >> sites/apps.txt
        touch .framework-ready
    fi
    bench pip install -e apps/helpdesk
    git -C apps/frappe remote set-url upstream https://github.com/frappe/frappe.git
    bench set-mariadb-host mariadb
    bench set-redis-cache-host redis://redis:6379
    bench set-redis-queue-host redis://redis:6379
    bench set-redis-socketio-host redis://redis:6379
    bench set-config -g webserver_port "$HTTP_PORT"
    bench set-config -g socketio_port "$SOCKETIO_PORT"
    printf 'y\n' | bench setup procfile
    sed -i '/^redis/d; /^watch/d' Procfile

    if [ ! -d apps/telephony ]; then
        bench get-app --skip-assets --branch develop https://github.com/frappe/telephony.git
    fi
    git -C apps/telephony fetch --depth 1 upstream "$TELEPHONY_REVISION"
    git -C apps/telephony checkout --detach "$TELEPHONY_REVISION"
    if [ ! -e apps/helpdesk ]; then
        ln -s /workspace apps/helpdesk
    fi
    bench pip install -e apps/telephony -e apps/helpdesk
    grep -qxF helpdesk sites/apps.txt || echo helpdesk >> sites/apps.txt
    yarn --cwd apps/helpdesk install --frozen-lockfile --ignore-scripts
    yarn --cwd apps/helpdesk/desk install --frozen-lockfile
    bench build

    if [ ! -f "sites/$SITE_NAME/site_config.json" ]; then
        bench new-site "$SITE_NAME" --db-root-password "$DB_ROOT_PASSWORD" \
            --admin-password "$ADMIN_PASSWORD" --mariadb-user-host-login-scope='%'
    fi
    bench --site "$SITE_NAME" install-app telephony
    bench --site "$SITE_NAME" install-app helpdesk
    bench --site "$SITE_NAME" set-config developer_mode 1
    bench --site "$SITE_NAME" set-config mute_emails 1
    bench --site "$SITE_NAME" set-config allow_demo_seed 1
    bench --site "$SITE_NAME" set-config host_name "http://$SITE_NAME:$HTTP_PORT"
    bench --site "$SITE_NAME" enable-scheduler
    bench use "$SITE_NAME"
    touch .bench-ready
fi
exec bench start
