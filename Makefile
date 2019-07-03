all: ami frontend sls-deploy

frontend: frontend/src/*
	cd frontend && PUBLIC_URL=/dev/ npm run build
	@rm -r launch/static/
	cp -R frontend/build/ launch/static/

ami: ami/*
	cd ami && packer build minecraft.json

sls-deploy: launch/*.py launch/serverless.yml launch/static
	cd launch && pipenv run sls deploy

.PHONY: ami sls-deploy frontend
