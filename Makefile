launch/static: frontend/src/*
	cd frontend && PUBLIC_URL=/dev/ npm run build
	rm -r launch/static/
	cp -R frontend/build/ launch/static/
