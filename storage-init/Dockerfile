FROM alpine:latest
RUN apk add --no-cache bash
COPY storage-init/init-storage.sh /init-storage.sh
RUN chmod +x /init-storage.sh
ENTRYPOINT ["/init-storage.sh"]
