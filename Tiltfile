docker_compose(
  './compose.yml',
  profiles=['shopify', 'exporter'] + 
    (['grafana'] if bool(os.getenv('WITH_OTEL', False)) else [])
)
