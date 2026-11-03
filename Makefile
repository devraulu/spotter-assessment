.PHONY: dev be fe test

dev:
	$(MAKE) -j2 be fe

be:
	cd backend && uv run manage.py runserver 8000

fe:
	cd web && pnpm dev

test:
	cd backend && uv run pytest
