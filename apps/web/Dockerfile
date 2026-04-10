FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
# Source code is mounted as a live volume at runtime (dev mode)
EXPOSE 3000
CMD ["npm", "run", "dev"]
