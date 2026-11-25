SHOTSCRAPER = uvx --from shot-scraper shot-scraper
# Your installed Google Chrome. Use SHOT_BROWSER=chromium for Playwright's (`make install`).
# Not BROWSER: that's usually set in the environment, to open URLs.
SHOT_BROWSER ?= chrome
# prod (app.readthedocs.org/.com) or dev (devthedocs.org/.com, for features that aren't deployed yet)
ENV ?= prod
# Where images are written: docs/user
OUT ?= ../..

include $(ENV).env
VARS := $(shell sed -n 's/^\([A-Z_]*\)=.*/\1/p' $(ENV).env) OUT HELPERS
export $(VARS)
AUTH_SUFFIX := $(if $(filter prod,$(ENV)),,-$(ENV))
RENDERED := build/$(ENV)
# --fail: stop on pages with errors, like a wrong ID or Cloudflare's rate limit (429)
MULTI = $(SHOTSCRAPER) multi -b $(SHOT_BROWSER) --log-console --fail

all: community business

clean:
	-rm -r build
	-rm auth-*.json

install:
	$(SHOTSCRAPER) install -b chromium

auth-business$(AUTH_SUFFIX).json:
	@echo "###################################################################"
	@echo "Authenticate as the rtfd-qa user on with a GitHub connected account"
	@echo "###################################################################"
	$(SHOTSCRAPER) auth -b $(SHOT_BROWSER) $(BUSINESS_URL)/accounts/login/ $@
auth-community$(AUTH_SUFFIX).json:
	@echo "###################################################################"
	@echo "Authenticate as the rtfd-qa user on with a GitHub connected account"
	@echo "###################################################################"
	$(SHOTSCRAPER) auth -b $(SHOT_BROWSER) $(COMMUNITY_URL)/accounts/login/ $@

# Fill in the variables from $(ENV).env and the shared helpers.js.
# Always rendered, so OUT and other command line variables apply.
$(RENDERED)/%.yml: %.yml FORCE
	@mkdir -p $(@D)
	HELPERS="$$(envsubst '$(foreach v,$(VARS),$$$(v))' < helpers.js | sed '2,$$s/^/    /')" \
		envsubst '$(foreach v,$(VARS),$$$(v))' < $< > $@

# One session for both sites, so a screenshot can borrow data from the other one
$(RENDERED)/auth.json: FORCE
	@mkdir -p $(@D)
	jq -s '{cookies: (map(.cookies) | add), origins: (map(.origins // []) | add)}' \
		$$(ls auth-community$(AUTH_SUFFIX).json auth-business$(AUTH_SUFFIX).json 2>/dev/null) > $@

# Community screenshots taking data from Business need that login too
COMMUNITY_AUTH := auth-community$(AUTH_SUFFIX).json \
	$(if $(filter $(BUSINESS_URL),$(INTEGRATION_SITE) $(SUBPROJECT_SITE)),auth-business$(AUTH_SUFFIX).json)

community: $(RENDERED)/community.yml $(RENDERED)/community-retina.yml $(COMMUNITY_AUTH) $(RENDERED)/auth.json
	$(MULTI) --auth $(RENDERED)/auth.json $(RENDERED)/community.yml
	$(MULTI) --auth $(RENDERED)/auth.json --retina $(RENDERED)/community-retina.yml

business: $(RENDERED)/business.yml auth-business$(AUTH_SUFFIX).json $(RENDERED)/auth.json
	$(MULTI) --auth $(RENDERED)/auth.json $(RENDERED)/business.yml

FORCE:
.PHONY: all clean install community business FORCE
