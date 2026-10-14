# Remoto image = upstream image + Remoto branding, installed on every start.
ARG HA_VERSION=stable
FROM ghcr.io/home-assistant/home-assistant:${HA_VERSION}

COPY custom_components/remoto_branding /opt/remoto/remoto_branding
COPY docker/configuration.yaml /opt/remoto/configuration.yaml
COPY --chmod=0755 docker/replace-default-config.sh /opt/remoto/replace-default-config.sh
# s6-overlay runs legacy cont-init scripts before the main service starts.
COPY --chmod=0755 docker/remoto-init.sh /etc/cont-init.d/10-remoto.sh

LABEL org.opencontainers.image.title="Remoto" \
      org.opencontainers.image.source="https://github.com/EKT-Tech-Org/remoto-branding"
