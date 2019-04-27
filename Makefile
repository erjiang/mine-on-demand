launch/static: frontend/src/*
	cd frontend && PUBLIC_URL=/dev/ npm run build
	cp -R frontend/build/ launch/static/
