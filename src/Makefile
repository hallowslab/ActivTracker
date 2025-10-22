.PHONY: all check render ssl static db secret nginx systemd clean

include .env

all: check render ssl static db secret nginx systemd

check:
	@command -v openssl >/dev/null 2>&1 || { echo "ERROR: openssl not installed. Please install openssl first."; exit 1; }
	@command -v nginx >/dev/null 2>&1 || { echo "ERROR: nginx not installed. Please install nginx first."; exit 1; }

render:
ifeq ($(ENABLE_SSL),true)
	uv run python scripts/render_templates.py --templates deploy/templates/activitytracker.nginx.ssl.template --out deploy/rendered --env src/.env
	mv deploy/rendered/activitytracker.nginx.ssl deploy/rendered/activitytracker.nginx
else
	uv run python scripts/render_templates.py --templates deploy/templates/activitytracker.nginx.http.template --out deploy/rendered --env src/.env
endif
	uv run python scripts/render_templates.py --templates deploy/templates/activitytracker.service.template --out deploy/rendered --env src/.env

ssl:
ifeq ($(ENABLE_SSL),true)
	mkdir -p deploy/ssl
	openssl req -x509 -nodes -newkey rsa:2048 \
		-keyout deploy/ssl/$(DOMAIN).key \
		-out deploy/ssl/$(DOMAIN).crt \
		-days 3650 \
		-subj "/CN=$(DOMAIN)/O=ActivTracker/C=XX"

	# Copy to SSL_DIR if defined
	if [ -n "$(SSL_DIR)" ]; then \
		sudo mkdir -p $(SSL_DIR); \
		sudo cp deploy/ssl/$(DOMAIN).crt $(SSL_DIR)/; \
		sudo cp deploy/ssl/$(DOMAIN).key $(SSL_DIR)/; \
		sudo chown root:root $(SSL_DIR)/$(DOMAIN).crt $(SSL_DIR)/$(DOMAIN).key; \
		sudo chmod 644 $(SSL_DIR)/$(DOMAIN).crt; \
		sudo chmod 600 $(SSL_DIR)/$(DOMAIN).key; \
	fi
endif

static:
	sudo mkdir -p $(STATIC_ROOT)
	sudo chown -R $(USER):www-data $(STATIC_ROOT)
	sudo chmod -R 755 $(STATIC_ROOT)
	uv run flask collect-static

db:
	uv run python create_db.py

secret:
	uv run python generate_secret.py

nginx:
	sudo cp deploy/rendered/activitytracker.nginx /etc/nginx/sites-available/activitytracker
	sudo ln -sf /etc/nginx/sites-available/activitytracker /etc/nginx/sites-enabled/activitytracker
	sudo nginx -t && sudo systemctl reload nginx

systemd:
	sudo cp deploy/rendered/activitytracker.service /etc/systemd/system/activitytracker.service
	sudo systemctl daemon-reload
	sudo systemctl enable --now activitytracker

clean:
	sudo systemctl stop activitytracker || true
	sudo rm -f deploy/ssl/$(DOMAIN).{crt,key}
	sudo rm -f /etc/systemd/system/activitytracker.service
	sudo rm -f /etc/nginx/sites-available/activitytracker
	sudo rm -f /etc/nginx/sites-enabled/activitytracker
	sudo systemctl daemon-reload
	sudo nginx -t && sudo systemctl reload nginx || true
