FROM node:18-alpine
WORKDIR /app
COPY package.json vite.config.js ./
COPY src ./src
COPY index.html ./
RUN npm install && npm run build
RUN npm install -g serve
CMD ["serve", "-s", "dist", "-l", "3000"] 