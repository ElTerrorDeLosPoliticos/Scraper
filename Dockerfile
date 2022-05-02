FROM python:3.8

COPY . /app

WORKDIR /app

ENV DATASETTE_SECRET '8d6e7036b2eab38ca5c3aa8fc0c3fbfc5673554e1b07941b2d81b081a3ae8b42'

RUN pip install -U datasette

RUN datasette inspect registro_visitas.db --inspect-file inspect-data.json

ENV PORT 8001

EXPOSE 8001

CMD datasette serve --host 0.0.0.0 -i registro_visitas.db --cors --inspect-file inspect-data.json --metadata metadata.yml --setting suggest_facets off  --port $PORT
