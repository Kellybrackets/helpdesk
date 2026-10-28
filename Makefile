.PHONY: configure up logs seed shell build migrate verify down
configure:
	python3 scripts/configure_dev.py
up: configure
	docker compose up -d
logs:
	docker compose logs -f --tail=100 frappe
seed:
	docker compose exec -T -w /home/frappe/frappe-bench frappe bench --site helpdesk.localhost execute helpdesk.demo.seed.run
shell:
	docker compose exec -w /home/frappe/frappe-bench frappe bash
build:
	docker compose exec -T -w /home/frappe/frappe-bench frappe bench build --app helpdesk
migrate:
	docker compose exec -T -w /home/frappe/frappe-bench frappe bench --site helpdesk.localhost migrate
verify:
	python3 scripts/verify_http.py
down:
	docker compose down
