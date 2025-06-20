SHOTSCRAPER=uvx --from shot-scraper shot-scraper

all: reqs screenshots

reqs: install auth-business.json auth-community.json
screenshots: business community

clean:
	-rm *.png
	-rm auth-*.json

install:
	$(SHOTSCRAPER) install
auth-business.json:
	$(SHOTSCRAPER) auth https://app.readthedocs.com/accounts/login/ $@
auth-community.json:
	$(SHOTSCRAPER) auth https://app.readthedocs.org/accounts/login/ $@

business: business.yml auth-business.json
	$(SHOTSCRAPER) \
		multi \
		--auth auth-business.json \
		--no-clobber \
		--log-console \
		business.yml

community: community.yml auth-community.json
	$(SHOTSCRAPER) \
		multi \
		--auth auth-community.json \
		--no-clobber \
		--log-console \
		community.yml
