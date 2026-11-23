# DeerFlow edge proxy for Railway: one public domain, split between the
# Next.js frontend and the Gateway API, as upstream's docker/nginx does.
# Same nginx build upstream pins in docker/docker-compose.yaml, plus a digest.
FROM nginx:1.31.2-alpine@sha256:54f2a904c251d5a34adf545a72d32515a15e08418dae0266e23be2e18c66fefa
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf.template /etc/deerflow/nginx.conf.template
COPY start.sh /usr/local/bin/deerflow-proxy
RUN chmod 0755 /usr/local/bin/deerflow-proxy
ENV PORT=8080
EXPOSE 8080
ENTRYPOINT []
CMD ["/usr/local/bin/deerflow-proxy"]
