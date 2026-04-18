FROM python:3.11-alpine


ARG WITH_OTEL
ENV WITH_OTEL=$WITH_OTEL

WORKDIR /work

COPY test.requirements.txt requirements.txt

ARG DUCKDB_BUILD_DEPENDENCIES="musl-dev linux-headers"
RUN \
  apk add --no-cache g++ $DUCKDB_BUILD_DEPENDENCIES && \
  python -m pip install --upgrade pip && \
  python -m pip install -r requirements.txt

RUN apk del $DUCKDB_BUILD_DEPENDENCIES

COPY ./patches.sh .
RUN \
  ./patches.sh && \
  rm ./patches.sh

COPY --parents \
  cogs/ ibis/ tests/ \
  .coveragerc .pylintrc .pytest.ini test-docker-entrypoint.sh \
  ./

RUN [[ -z "$WITH_OTEL" ]] || .local/bin/opentelemetry-bootstrap --action=install

ENTRYPOINT [ "/work/test-docker-entrypoint.sh" ]
