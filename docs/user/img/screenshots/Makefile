SHOTSCRAPER=uvx --from shot-scraper shot-scraper

all: reqs screenshots

reqs: install auth-business.json auth-community.json
screenshots: business community

clean:
	-rm *.png
	-rm auth-*.json

install:
	$(SHOTSCRAPER) install -b chromium
auth-business.json:
	@echo "###################################################################"
	@echo "Authenticate as the rtfd-qa user on with a GitHub connected account"
	@echo "###################################################################"
	$(SHOTSCRAPER) auth https://app.readthedocs.com/accounts/login/ $@
auth-community.json:
	@echo "###################################################################"
	@echo "Authenticate as the rtfd-qa user on with a GitHub connected account"
	@echo "###################################################################"
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
