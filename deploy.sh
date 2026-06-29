#!/bin/bash
set -e

echo "=========================================="
echo "  Gate Cars - سكربت النشر على السيرفر"
echo "=========================================="

# ---- المتغيرات ----
SITE_NAME="gatecar"
ADMIN_PASS="admin"
DB_ROOT_PASS="123"
GITHUB_REPO="https://github.com/ziadSuleyman/GateCar.git"

echo ""
echo "[1/7] تنظيف Docker القديم..."
docker stop $(docker ps -aq) 2>/dev/null || true
docker rm $(docker ps -aq) 2>/dev/null || true
docker system prune -af --volumes 2>/dev/null || true
echo "✓ تم التنظيف"

echo ""
echo "[2/7] تثبيت المتطلبات..."
apt update -y && apt install -y git curl docker.io docker-compose-plugin
systemctl enable docker && systemctl start docker
echo "✓ تم تثبيت المتطلبات"

echo ""
echo "[3/7] إنشاء مجلد المشروع..."
mkdir -p /opt/gatecar && cd /opt/gatecar

# إنشاء docker-compose.yml
cat > docker-compose.yml << 'COMPOSE'
services:
  mariadb:
    image: mariadb:11.4
    restart: always
    environment:
      MYSQL_ROOT_PASSWORD: 123
      MYSQL_CHARACTER_SET_SERVER: utf8mb4
      MYSQL_COLLATION_SERVER: utf8mb4_unicode_ci
    volumes:
      - mariadb-data:/var/lib/mysql
    command: ['--character-set-server=utf8mb4', '--collation-server=utf8mb4_unicode_ci', '--skip-character-set-client-handshake']

  redis-cache:
    image: redis:7-alpine
    restart: always

  redis-queue:
    image: redis:7-alpine
    restart: always

  frappe:
    image: frappe/bench:latest
    restart: always
    depends_on:
      - mariadb
      - redis-cache
      - redis-queue
    ports:
      - "8080:8000"
    volumes:
      - frappe-data:/home/frappe/frappe-bench
    stdin_open: true
    tty: true

volumes:
  mariadb-data:
  frappe-data:
COMPOSE

echo "✓ تم إنشاء docker-compose.yml"

echo ""
echo "[4/7] تشغيل الحاويات..."
docker compose up -d
echo "انتظار بدء الحاويات..."
sleep 15
echo "✓ الحاويات تعمل"

echo ""
echo "[5/7] إعداد Frappe bench..."
CONTAINER=$(docker compose ps -q frappe)

docker exec -u frappe $CONTAINER bash -c "
  cd /home/frappe && \
  bench init frappe-bench --frappe-branch version-16 --skip-redis-config-generation && \
  cd frappe-bench && \
  bench set-config -g db_host mariadb && \
  bench set-config -g redis_cache redis://redis-cache:6379 && \
  bench set-config -g redis_queue redis://redis-queue:6379 && \
  bench set-config -g redis_socketio redis://redis-cache:6379 && \
  bench set-config -g developer_mode 1
"
echo "✓ تم إعداد Frappe"

echo ""
echo "[6/7] تثبيت التطبيقات..."
docker exec -u frappe $CONTAINER bash -c "
  cd /home/frappe/frappe-bench && \
  bench get-app erpnext --branch version-16 && \
  bench get-app hrms --branch version-16 && \
  bench get-app payments --branch version-16 && \
  bench get-app $GITHUB_REPO && \
  bench new-site $SITE_NAME \
    --db-root-password $DB_ROOT_PASS \
    --admin-password $ADMIN_PASS \
    --install-app erpnext \
    --install-app hrms \
    --install-app payments && \
  bench --site $SITE_NAME install-app gatecar && \
  bench --site $SITE_NAME set-config developer_mode 1 && \
  bench use $SITE_NAME
"
echo "✓ تم تثبيت التطبيقات"

echo ""
echo "[7/7] بناء وتشغيل..."
docker exec -u frappe $CONTAINER bash -c "
  cd /home/frappe/frappe-bench && \
  bench build && \
  bench migrate
"

# تشغيل bench start في الخلفية
docker exec -u frappe -d $CONTAINER bash -c "
  cd /home/frappe/frappe-bench && bench start
"

echo ""
echo "=========================================="
echo "  ✓ تم النشر بنجاح!"
echo "=========================================="
echo ""
echo "  الرابط: http://$(hostname -I | awk '{print $1}'):8080"
echo "  المستخدم: Administrator"
echo "  كلمة المرور: $ADMIN_PASS"
echo ""
echo "  لتغيير كلمة المرور:"
echo "  docker exec -u frappe \$CONTAINER bash -c 'cd frappe-bench && bench --site $SITE_NAME set-admin-password NEW_PASSWORD'"
echo ""
